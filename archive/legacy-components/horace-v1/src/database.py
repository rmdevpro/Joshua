# src/database.py
import asyncpg
from typing import List, Dict, Any, Optional
from uuid import UUID
from .config import config
from .utils.logger import logger

class Database:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        logger.info(f"Connecting to database at {config.DB_HOST}:{config.DB_PORT}...")
        try:
            self._pool = await asyncpg.create_pool(
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                host=config.DB_HOST,
                port=config.DB_PORT,
            )
            logger.info("Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise

    async def disconnect(self):
        if self._pool:
            logger.info("Closing database connection pool...")
            await self._pool.close()
            logger.info("Database connection pool closed.")

    async def fetchrow(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query, *args):
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    # --- File Operations ---
    async def find_file_by_id(self, file_id: UUID) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_files WHERE id = $1", file_id)

    async def find_file_by_checksum(self, checksum: str) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_files WHERE checksum = $1 AND status != 'deleted'", checksum)

    async def insert_file(self, file_data: Dict[str, Any]) -> asyncpg.Record:
        query = """
            INSERT INTO horace_files (file_path, owner, purpose, tags, size, mime_type, checksum, collection_id, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        return await self.fetchrow(
            query,
            file_data['file_path'], file_data['owner'], file_data.get('purpose'),
            file_data.get('tags', []), file_data['size'], file_data['mime_type'],
            file_data['checksum'], file_data.get('collection_id'), file_data.get('correlation_id')
        )
    
    async def update_file(self, file_id: UUID, update_data: Dict[str, Any]) -> Optional[asyncpg.Record]:
        # Whitelist allowed fields to prevent SQL injection
        ALLOWED_FIELDS = {'tags', 'purpose', 'status', 'collection_id', 'checksum', 'size', 'current_version', 'metadata', 'correlation_id'}

        fields, values = [], []
        for i, (key, value) in enumerate(update_data.items(), 1):
            if key not in ALLOWED_FIELDS:
                raise ValueError(f"Invalid field for update: {key}")

            # Use JSONB merge operator for metadata field
            if key == 'metadata':
                fields.append(f"metadata = metadata || ${i}")
            else:
                fields.append(f"{key} = ${i}")
            values.append(value)

        fields.append(f"updated_at = NOW()")
        set_clause = ", ".join(fields)

        query = f"UPDATE horace_files SET {set_clause} WHERE id = ${len(values) + 1} RETURNING *"
        return await self.fetchrow(query, *values, file_id)

    # --- Version Operations ---
    async def insert_version(self, version_data: Dict[str, Any]) -> asyncpg.Record:
        query = """
            INSERT INTO horace_versions (file_id, version, size, checksum, version_path)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        return await self.fetchrow(
            query, version_data['file_id'], version_data['version'], version_data['size'],
            version_data['checksum'], version_data['version_path']
        )
    
    async def get_versions_for_file(self, file_id: UUID) -> List[asyncpg.Record]:
        query = "SELECT * FROM horace_versions WHERE file_id = $1 ORDER BY version DESC"
        return await self.fetch(query, file_id)
    
    async def get_oldest_version(self, file_id: UUID) -> Optional[asyncpg.Record]:
        query = "SELECT * FROM horace_versions WHERE file_id = $1 ORDER BY version ASC LIMIT 1"
        return await self.fetchrow(query, file_id)

    async def delete_version(self, version_id: UUID):
        await self.execute("DELETE FROM horace_versions WHERE id = $1", version_id)

    # --- Collection Operations ---
    async def find_collection_by_name(self, name: str) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_collections WHERE name = $1", name)
        
    async def find_collection_by_id(self, col_id: UUID) -> Optional[asyncpg.Record]:
        return await self.fetchrow("SELECT * FROM horace_collections WHERE id = $1", col_id)

    async def insert_collection(self, name: str, description: str, metadata: Dict) -> asyncpg.Record:
        query = """
            INSERT INTO horace_collections (name, description, metadata)
            VALUES ($1, $2, $3)
            ON CONFLICT (name) DO UPDATE SET
                description = EXCLUDED.description,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING *
        """
        return await self.fetchrow(query, name, description, metadata)
    
    async def get_collection_file_count(self, collection_id: UUID) -> int:
        res = await self.fetchrow("SELECT COUNT(*) FROM horace_files WHERE collection_id = $1", collection_id)
        return res['count'] if res else 0

    async def list_collections(self, limit: int, offset: int) -> (int, List[asyncpg.Record]):
        total_query = "SELECT COUNT(*) FROM horace_collections"
        total = (await self.fetchrow(total_query))['count']
        
        list_query = "SELECT * FROM horace_collections ORDER BY name ASC LIMIT $1 OFFSET $2"
        collections = await self.fetch(list_query, limit, offset)
        
        return total, collections

    # --- Search ---
    async def search_files(self, params: Dict[str, Any]) -> (int, List[asyncpg.Record]):
        query_base = "FROM horace_files WHERE"
        conditions = []
        args = []
        
        # Default status to 'active' if not provided
        status = params.get('query', {}).get('status', 'active')
        conditions.append(f"status = ${len(args) + 1}")
        args.append(status)

        q = params.get('query', {})
        if q.get('tags'):
            conditions.append(f"tags @> ${len(args) + 1}")
            args.append(q['tags'])
        if q.get('owner'):
            conditions.append(f"owner = ${len(args) + 1}")
            args.append(q['owner'])
        if q.get('created_after'):
            conditions.append(f"created_at >= ${len(args) + 1}")
            args.append(q['created_after'])
        if q.get('created_before'):
            conditions.append(f"created_at <= ${len(args) + 1}")
            args.append(q['created_before'])
        if q.get('file_type'):
            conditions.append(f"(mime_type LIKE ${len(args) + 1} OR file_path LIKE ${len(args) + 1})")
            args.append(f"%{q['file_type']}%")
        if q.get('min_size') is not None:
            conditions.append(f"size >= ${len(args) + 1}")
            args.append(q['min_size'])
        if q.get('max_size') is not None:
            conditions.append(f"size <= ${len(args) + 1}")
            args.append(q['max_size'])
        if q.get('collection'):
            collection_rec = await self.find_collection_by_name(q['collection'])
            if collection_rec:
                conditions.append(f"collection_id = ${len(args) + 1}")
                args.append(collection_rec['id'])
            else: # Collection not found, return no results
                return 0, []

        where_clause = " AND ".join(conditions)
        
        # Count total matching results
        count_query = f"SELECT COUNT(*) {query_base} {where_clause}"
        total = (await self.fetchrow(count_query, *args))['count']
        
        # Fetch paginated results
        # Whitelist allowed columns for sorting to prevent SQL injection
        allowed_sort_columns = [
            'created_at', 'updated_at', 'size', 'owner', 'mime_type', 'file_path', 'status'
        ]
        sort_by = params.get('sort_by', 'created_at')
        if sort_by not in allowed_sort_columns:
            sort_by = 'created_at'  # Default to safe column

        # Whitelist allowed order directions
        order = params.get('order', 'desc').upper()
        if order not in ['ASC', 'DESC']:
            order = 'DESC'  # Default to safe direction

        limit = params.get('limit', 50)
        offset = params.get('offset', 0)

        results_query = f"""
            SELECT * {query_base} {where_clause}
            ORDER BY "{sort_by}" {order}
            LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}
        """
        results = await self.fetch(results_query, *args, limit, offset)
        
        return total, results
