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
                token           varchar(80) PRIMARY KEY,
                refresh_token   varchar(80) NOT NULL,
                token_due_date  date NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS odoo_instances (
                owner           varchar(80) REFERENCES users(token)
                    ON UPDATE CASCADE,
                url             varchar(140),
                db_name         varchar(80),
                db_password     varchar(80),
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
        try:
            await self.conn.execute("""
                INSERT INTO users (token, refresh_token, token_due_date)
                    VALUES ($1, $2, $3);
            """, token, refresh_token, token_due_date)
        except asyncpg.exceptions.UniqueViolationError:
            raise UserAlreadyExists("User with this token already exists.")

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
        try:
            await self.conn.execute("""
                INSERT INTO odoo_instances 
                    (owner, url, db_name, db_password, next_backup, cooldown)
                VALUES($1, $2, $3, $4, current_date, $5);
            """, user_token, instance_url, db_name, db_password, cooldown)
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise UserExistenceError("User with this token doesn't exist.")
        except asyncpg.exceptions.UniqueViolationError:
            raise OdooInstanceAlreadyExistsError(
                "Odoo instance with this owner, "
                "url and database name already exists."
            )

    async def odoo_instance_exists(
            self, user_token: str,
            url: str,
            db_name: str) -> bool:
        return bool(await self.conn.fetchval("""
            SELECT count(*)
            FROM odoo_instances
            WHERE owner = $1 AND url = $2 AND db_name = $3;
        """, user_token, url, db_name))

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
        async with self.conn.transaction():
            res = await self.conn.fetch("""
                SELECT owner, url, db_name, db_password
                FROM odoo_instances
                WHERE next_backup <= current_date;
            """)
            await self.conn.execute("""
                UPDATE odoo_instances
                SET next_backup = current_date + cooldown
                WHERE next_backup <= current_date;
            """)
        return [{
            "token": record["owner"],
            "url": record["url"],
            "db_name": record["db_name"],
            "db_password": record["db_password"]
        } for record in res]

    async def get_tokens_to_refresh(self) -> list[dict[str, str]]:
        res = await self.conn.fetch("""
            SELECT token, refresh_token
            FROM users
            WHERE current_date > users.token_due_date - 30;
        """)
        return [{
            "token": record["token"],
            "refresh_token": record["refresh_token"]
        } for record in res]

    async def update_user_token(
            self,
            previous_token: str,
            new_token: str,
            new_refresh_token: str,
            new_due_date: date) -> None:
        try:
            async with self.conn.transaction():
                await self.conn.execute("""
                    UPDATE users
                    SET token_due_date = $2
                    WHERE token = $1;
                """, previous_token, new_due_date)
                await self.conn.execute("""
                    UPDATE users as u SET
                        token = nd.token,
                        refresh_token = nd.refresh_token
                    FROM (VALUES
                        ($1, $2, $3)
                    ) as nd(prev_token, token, refresh_token)
                    WHERE u.token = nd.prev_token;
                """, previous_token, new_token, new_refresh_token)
        except asyncpg.exceptions.UniqueViolationError:
            raise UserAlreadyExists("User with this token already exists.")


class UserExistenceError(Exception):
    pass


class OdooInstanceAlreadyExistsError(Exception):
    pass


class UserAlreadyExists(Exception):
    pass
