__author__ = "Itamar Dalal"

import sqlite3
from hashlib import sha256
from secrets import token_bytes
from time import time
from settings import Settings
import requests
import re
from dnslib import DNSRecord, QTYPE
from datetime import datetime
import logging
from typing import Set, List
from socket import gethostbyname, gaierror

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UsersDBHandler:
    SALT_LENGTH = 8
    PEPPER = b"my_secret_pepper"

    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users (
                                    username TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    email TEXT UNIQUE NOT NULL,
                                    password TEXT NOT NULL,
                                    salt TEXT NOT NULL)"""
            )
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def is_username_exist(self, username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            return cursor.fetchone() is not None

    def is_email_exist(self, email):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            return cursor.fetchone() is not None

    def get_email(self, username):
        if not self.is_username_exist(username):
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username=?", (username,))
            email = cursor.fetchone()[0]
            return email

    def get_username(self, email) -> str:
        if not self.is_email_exist(email):
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE email=?", (email,))
            username = cursor.fetchone()[0]
            return username

    def is_password_ok(self, username, password):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password, salt FROM users WHERE username=?", (username,)
            )
            stored_password, stored_salt = cursor.fetchone()

            if stored_password:
                hashed_password = sha256(
                    password.encode() + stored_salt + UsersDBHandler.PEPPER
                ).hexdigest()
                return hashed_password == stored_password
            return False

    def save_user(self, username, email, password) -> None:
        salt = token_bytes(UsersDBHandler.SALT_LENGTH)
        hashed_password = sha256(
            password.encode() + salt + UsersDBHandler.PEPPER
        ).hexdigest()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password, salt) VALUES (?, ?, ?, ?)",
                (username, email, hashed_password, salt),
            )
            conn.commit()

    def update_user_password(self, username, new_password) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt FROM users WHERE username=?", (username,))
            stored_salt = cursor.fetchone()[0]
            hashed_password = sha256(
                new_password.encode() + stored_salt + UsersDBHandler.PEPPER
            ).hexdigest()
            cursor.execute(
                "UPDATE users SET password=? WHERE username=?", (hashed_password, username)
            )
            conn.commit()

    def delete_user(self, username) -> None:
        if self.is_username_exist(username):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username=?", (username,))
                conn.commit()


class EmailCodeDBHandler:
    TIMEOUT = Settings.EMAIL_CODE_TIMEOUT.value  # 5 minutes

    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()
        self.clean_expired_codes()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS emails (
                                    email TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    timeout FLOAT NOT NULL)"""
            )
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def is_email_exist(self, email) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE email=?", (email,))
            return cursor.fetchone() is not None

    def is_timeout_passed(self, email) -> bool:
        if not self.is_email_exist(email):
            return True
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timeout FROM emails WHERE email=?", (email,))
            timeout = datetime.fromtimestamp(cursor.fetchone()[0]).timestamp()
            return time() > timeout

    def save_email(self, email) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO emails (email, timeout) VALUES (?, ?)",
                (email, time() + EmailCodeDBHandler.TIMEOUT),
            )
            conn.commit()

    def delete_email(self, email) -> None:
        if self.is_email_exist(email):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM emails WHERE email=?", (email,))
                conn.commit()

    def clean_expired_codes(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emails WHERE timeout < ?", (time(),))
            conn.commit()

    def delete_table(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS emails")
            conn.commit()


class DomainsDBHandler:
    # Configuration for dataset expansion
    DATASET_URLS = [
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/lists/pro.txt",
    ]
    BLOCKLIST_SOURCE = "external_dataset"

    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS domains (
                                    domain TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    username TEXT NOT NULL,
                                    time FLOAT NOT NULL
                )"""
            )

            cursor.execute("PRAGMA table_info(domains)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'source' not in columns:
                cursor.execute("ALTER TABLE domains ADD COLUMN source TEXT")
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_domain(self, domain, username, source="user") -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO domains (domain, username, time, source) VALUES (?, ?, ?, ?)",
                (domain, username, time(), source),
            )
            conn.commit()
    
    def remove_domain(self, domain) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM domains WHERE domain=?", (domain,))
            conn.commit()

    def is_domain_exist(self, domain) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM domains WHERE domain=?", (domain,))
            return cursor.fetchone() is not None
    
    def get_domains(self) -> set:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT domain FROM domains")
            return set([row[0] for row in cursor.fetchall()])

    @staticmethod
    def is_valid_domain(domain: str, use_dns_validation: bool = True) -> bool:
        """Validate domain format and optionally resolvability."""
        DOMAIN_REGEX = r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,})$"
        if not re.match(DOMAIN_REGEX, domain):
            logger.debug(f"Domain {domain} failed regex validation")
            return False
        
        if not use_dns_validation:
            return True
        
        try:
            gethostbyname(domain)
        except gaierror:
            return False
        return True

    def fetch_dataset(self, url: str) -> List[str]:
        """Fetch and parse domains from a dataset URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            domains = set()
            
            for line in response.text.splitlines():
                line = line.strip()
                # skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # handle hosts file format (e.g., "0.0.0.0 domain.com")
                if line.startswith(("0.0.0.0", "127.0.0.1")):
                    parts = line.split()
                    if len(parts) > 1:
                        domain = parts[1]
                else:
                    domain = line
                
                # clean and validate domain
                domain = domain.strip().lower()
                if self.is_valid_domain(domain, use_dns_validation=False):
                    domains.add(domain)
            
            return list(domains)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch dataset from {url}: {e}")
            return []

    def expand_domains_from_datasets(self, use_dns_validation: bool = False) -> int:
        """Expand the domain database with external datasets."""
        existing_domains = self.get_domains()
        new_domains_count = 0

        for url in self.DATASET_URLS:
            logger.info(f"Fetching dataset from {url}")
            domains = self.fetch_dataset(url)
            logger.info(f"Retrieved {len(domains)} domains from {url}")

            for domain in domains:
                if domain not in existing_domains:
                    self.save_domain(domain, "system", self.BLOCKLIST_SOURCE)
                    new_domains_count += 1
                    existing_domains.add(domain)
                    logger.debug(f"Added domain {domain}")
                else:
                    logger.debug(f"Skipped duplicate domain {domain}")

        logger.info(f"Added {new_domains_count} new domains to the database")
        return new_domains_count


if __name__ == "__main__":
    # Example usage:
    db_test = UsersDBHandler()
    # db_test.delete_user("itamar")
    
    domain_db = DomainsDBHandler()
    domain_db.expand_domains_from_datasets(use_dns_validation=False)
