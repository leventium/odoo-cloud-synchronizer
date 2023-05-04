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
                id              BIGINT PRIMARY KEY,
                token           VARCHAR(120) NOT NULL,
                refresh_token   VARCHAR(120) NOT NULL,
                token_due_date  DATE NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS odoo_instances (
                owner           BIGINT REFERENCES users(id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                url             VARCHAR(140),
                db_name         VARCHAR(80),
                db_password     VARCHAR(80) NOT NULL,
                next_backup     DATE NOT NULL,
                cooldown        INT NOT NULL,
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
            self, yandex_id: int,
            token: str,
            refresh_token: str,
            token_due_date: date) -> None:
        try:
            await self.conn.execute("""
                INSERT INTO users (id, token, refresh_token, token_due_date)
                    VALUES ($1, $2, $3, $4);
            """, yandex_id, token, refresh_token, token_due_date)
        except asyncpg.exceptions.UniqueViolationError:
            raise UserAlreadyExists("User with this id already exists.")
        except asyncpg.StringDataRightTruncationError:
            raise StringTooLong("String is too long.")

    async def user_exists(self, yandex_id: int) -> bool:
        return bool(await self.conn.fetchval("""
            SELECT count(*)
            FROM users
            WHERE id = $1;
        """, yandex_id))

    async def insert_odoo_instance(
            self, yandex_id: int,
            instance_url: str,
            db_name: str,
            db_password: str,
            cooldown: int) -> None:
        try:
            await self.conn.execute("""
                INSERT INTO odoo_instances 
                    (owner, url, db_name, db_password, next_backup, cooldown)
                VALUES($1, $2, $3, $4, current_date, $5);
            """, yandex_id, instance_url, db_name, db_password, cooldown)
        except asyncpg.ForeignKeyViolationError:
            raise UserExistenceError("User with this id doesn't exist.")
        except asyncpg.UniqueViolationError:
            raise OdooInstanceAlreadyExistsError(
                "Odoo instance with this owner, "
                "url and database name already exists."
            )
        except asyncpg.StringDataRightTruncationError:
            raise StringTooLong("String is too long.")

    async def odoo_instance_exists(
            self, yandex_id: int,
            url: str,
            db_name: str) -> bool:
        return bool(await self.conn.fetchval("""
            SELECT count(*)
            FROM odoo_instances
            WHERE owner = $1 AND url = $2 AND db_name = $3;
        """, yandex_id, url, db_name))

    async def get_instances_of_user(
            self, yandex_id: int) -> list[dict[str, str]]:
        res = await self.conn.fetch("""
            SELECT url, db_name
            FROM odoo_instances
            WHERE owner = $1;
        """, yandex_id)
        return [{
            "url": record["url"],
            "db_name": record["db_name"]
        } for record in res]

    async def delete_odoo_instance(
            self, yandex_id: int,
            instance_url: str,
            db_name: str) -> None:
        await self.conn.execute("""
            DELETE
            FROM odoo_instances
            WHERE owner = $1 AND url = $2 AND db_name = $3;
        """, yandex_id, instance_url, db_name)

    async def get_odoo_instances_to_backup(self) -> list[dict[str, str]]:
        async with self.conn.transaction():
            res = await self.conn.fetch("""
                SELECT token, url, db_name, db_password
                FROM odoo_instances oi LEFT JOIN users u ON u.id = oi.owner
                WHERE next_backup <= current_date;
            """)
            await self.conn.execute("""
                UPDATE odoo_instances
                SET next_backup = current_date + cooldown
                WHERE next_backup <= current_date;
            """)
        return [{
            "token": record["token"],
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
            yandex_id: int,
            new_token: str,
            new_refresh_token: str,
            new_due_date: date) -> None:
        async with self.conn.transaction():
            await self.conn.execute("""
                UPDATE users
                SET token_due_date = $2
                WHERE id = $1;
            """, yandex_id, new_due_date)
            await self.conn.execute("""
                UPDATE users as u SET
                    token = nd.token,
                    refresh_token = nd.refresh_token
                FROM (VALUES
                    ($1, $2, $3)
                ) as nd(id, token, refresh_token)
                WHERE u.id = nd.id;
            """, yandex_id, new_token, new_refresh_token)


class UserExistenceError(Exception):
    pass


class OdooInstanceAlreadyExistsError(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class StringTooLong(Exception):
    pass
