"""
Module providing interface to database.
"""
from datetime import date
import asyncpg


class Database:
    @staticmethod
    async def create_tables(
            host: str,
            port: int,
            username: str,
            password: str,
            database: str) -> None:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                token           varchar(160) PRIMARY KEY,
                refresh_token   varchar(160),
                token_due_date  date
            );
            
            CREATE TABLE IF NOT EXISTS odoo_instances (
                owner           varchar(80) REFERENCES users(token),
                url             varchar(80),
                db_name         varchar(60),
                db_password     varchar(60),
                next_backup     date,
                cooldown        int,
                PRIMARY KEY (owner, url, db_name)
            );
        """)
        await conn.close()

    @classmethod
    async def connect(
            cls, host: str,
            port: int,
            username: str,
            password: str,
            database: str):
        instance = cls()
        instance.conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        return instance

    async def close(self):
        await self.conn.close()

    async def insert_user(
            self, token: str,
            refresh_token: str,
            token_due_date: date) -> None:
        await self.conn.execute("""
            INSERT INTO users (token, refresh_token, token_due_date)
                VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;
        """, token, refresh_token, token_due_date)

    async def user_exists(self, token: str) -> bool:
        return bool(await self.conn.fetchval("""
            SELECT count(*)
                FROM users
                WHERE token = $1;
        """, token))

    async def insert_odoo_instance(
            self, user_token: str,
            instance_url: str,
            db_name: str,
            db_password: str,
            cooldown: int) -> None:
        await self.conn.execute("""
            INSERT INTO odoo_instances 
                    (owner, url, db_name, db_password, next_backup, cooldown)
                VALUES($1, $2, $3, $4, current_date, $5) ON CONFLICT DO NOTHING;
        """, user_token, instance_url, db_name, db_password, cooldown)

    async def odoo_instance_exists(self, owner: str, url: str, db_name: str):
        return bool(await self.conn.fetchval("""
            SELECT count(*)
                FROM odoo_instances
                WHERE owner = $1 AND url = $2 AND db_name = $3;
        """, owner, url, db_name))

    async def get_instances_of_user(
            self, user_token: str) -> list[dict[str, str]]:
        res = await self.conn.fetch("""
            SELECT url, db_name
                FROM odoo_instances
                WHERE owner = $1;
        """, user_token)
        return [{
            "url": record["url"],
            "db_name": record["db_name"]
        } for record in res]

    async def delete_odoo_instance(
            self, user_token: str,
            instance_url: str,
            db_name: str) -> None:
        await self.conn.execute("""
            DELETE
                FROM odoo_instances
                WHERE owner = $1 AND url = $2 AND db_name = $3;
        """, user_token, instance_url, db_name)

    async def get_odoo_instances_to_backup(self) -> list[dict[str, str]]:
        res = await self.conn.fetch("""
            SELECT owner, url, db_name, db_password
                FROM odoo_instances
                WHERE next_backup <= current_date;
        """)
        await self.conn.execute("""
            UPDATE
                SET next_backup = current_date + cooldown
                WHERE next_backup <= current_date;
        """)
        return [{
            "token": record["owner"],
            "url": record["url"],
            "db_name": record["db_name"],
            "db_password": record["db_password"]
        } for record in res]
