#!/usr/bin/env python3
"""
Sergey - Google Workspace MAD
Named after Sergey Brin, co-founder of Google

Provides comprehensive Google Workspace integration via MCP tools.
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import io
import mimetypes
from datetime import datetime, timedelta

# Google API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ICCM standard libraries
from joshua_network import Server as MCPServer, ToolError as MCPToolError
from joshua_logger import Logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize joshua_logger
jlogger = Logger()

class SergeyWorkspace:
    """Google Workspace integration manager"""

    def __init__(self, service_account_path: str):
        """Initialize Google services with service account"""
        self.service_account_path = service_account_path
        self.google_drive_service = None
        self.google_sheets_service = None
        self.google_docs_service = None
        self.google_slides_service = None
        self.google_calendar_service = None

    async def initialize(self):
        """Initialize all Google services"""
        try:
            await jlogger.log("INFO", "Initializing Sergey Google Workspace MAD", "sergey")

            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/presentations',
                    'https://www.googleapis.com/auth/calendar'
                ]
            )

            self.google_drive_service = build('drive', 'v3', credentials=credentials)
            self.google_sheets_service = build('sheets', 'v4', credentials=credentials)
            self.google_docs_service = build('docs', 'v1', credentials=credentials)
            self.google_slides_service = build('slides', 'v1', credentials=credentials)
            self.google_calendar_service = build('calendar', 'v3', credentials=credentials)

            await jlogger.log("INFO", "Google services initialized successfully", "sergey", data={"services": ["drive", "sheets", "docs", "slides", "calendar"]})
            logger.info("Sergey Google Workspace MAD initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize Google services: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await jlogger.log("ERROR", error_msg, "sergey", data={"error": str(e)})
            raise

    # ============ GOOGLE SHEETS OPERATIONS ============

    def _sheets_read_sync(self, sheet_id: str, range_name: str) -> dict:
        return self.google_sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=range_name
        ).execute()

    async def sheets_read(self, sheet_id: str, range_name: str = "A1:Z1000") -> dict:
        """Read data from a Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading sheet {sheet_id}", "sergey", data={"sheet_id": sheet_id, "range": range_name})

            result = await asyncio.to_thread(self._sheets_read_sync, sheet_id, range_name)

            values = result.get("values", [])
            await jlogger.log("INFO", f"Successfully read {len(values)} rows from sheet", "sergey")
            return {"sheet_id": sheet_id, "range": range_name, "values": values, "row_count": len(values)}
        except HttpError as e:
            error_msg = f"Google Sheets read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"sheet_id": sheet_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _sheets_write_sync(self, sheet_id: str, range_name: str, values: list) -> dict:
        body = {"values": values}
        return self.google_sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name, valueInputOption="RAW", body=body
        ).execute()

    async def sheets_write(self, sheet_id: str, range_name: str, values: list) -> dict:
        """Write data to a Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Writing to sheet {sheet_id}", "sergey", data={"sheet_id": sheet_id, "range": range_name, "rows": len(values)})

            result = await asyncio.to_thread(self._sheets_write_sync, sheet_id, range_name, values)

            await jlogger.log("INFO", f"Successfully wrote {result.get('updatedCells')} cells", "sergey")
            return {"sheet_id": sheet_id, "updated_cells": result.get("updatedCells"), "updated_range": result.get("updatedRange")}
        except HttpError as e:
            error_msg = f"Google Sheets write error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"sheet_id": sheet_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _sheets_create_sync(self, title: str) -> dict:
        body = {"properties": {"title": title}}
        return self.google_sheets_service.spreadsheets().create(body=body).execute()

    async def sheets_create(self, title: str) -> dict:
        """Create a new Google Sheet in a non-blocking way."""
        if not self.google_sheets_service:
            raise MCPToolError("Google Sheets service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new sheet: {title}", "sergey")

            result = await asyncio.to_thread(self._sheets_create_sync, title)

            await jlogger.log("INFO", "Successfully created sheet", "sergey", data={"sheet_id": result.get("spreadsheetId"), "title": title})
            return {"sheet_id": result.get("spreadsheetId"), "title": title, "url": result.get("spreadsheetUrl")}
        except HttpError as e:
            error_msg = f"Google Sheets create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE DOCS OPERATIONS ============

    def _docs_create_sync(self, title: str, content: Optional[str]) -> dict:
        doc_metadata = {'name': title, 'mimeType': 'application/vnd.google-apps.document'}
        doc = self.google_drive_service.files().create(body=doc_metadata, fields='id,name,webViewLink').execute()
        if content:
            requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
            self.google_docs_service.documents().batchUpdate(documentId=doc['id'], body={'requests': requests}).execute()
        return doc

    async def docs_create(self, title: str, content: Optional[str] = None) -> dict:
        """Create a new Google Document in a non-blocking way."""
        if not self.google_docs_service or not self.google_drive_service:
            raise MCPToolError("Google Docs/Drive services not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new document: {title}", "sergey")

            doc = await asyncio.to_thread(self._docs_create_sync, title, content)

            await jlogger.log("INFO", "Successfully created document", "sergey", data={"doc_id": doc['id'], "title": title})
            return {"doc_id": doc['id'], "title": doc['name'], "url": doc['webViewLink']}
        except HttpError as e:
            error_msg = f"Google Docs create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _docs_read_sync(self, doc_id: str) -> dict:
        return self.google_docs_service.documents().get(documentId=doc_id).execute()

    async def docs_read(self, doc_id: str) -> dict:
        """Read content from a Google Document in a non-blocking way."""
        if not self.google_docs_service:
            raise MCPToolError("Google Docs service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading document {doc_id}", "sergey")

            document = await asyncio.to_thread(self._docs_read_sync, doc_id)

            content_parts = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for para_elem in element.get('paragraph', {}).get('elements', []):
                        if 'textRun' in para_elem:
                            content_parts.append(para_elem['textRun'].get('content', ''))
            text_content = ''.join(content_parts)

            await jlogger.log("INFO", "Successfully read document", "sergey", data={"doc_id": doc_id, "length": len(text_content)})
            return {"doc_id": doc_id, "title": document.get('title'), "content": text_content, "revision_id": document.get('revisionId')}
        except HttpError as e:
            error_msg = f"Google Docs read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"doc_id": doc_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _docs_get_end_index_sync(self, doc_id: str) -> int:
        doc = self.google_docs_service.documents().get(documentId=doc_id, fields='body(content(endIndex))').execute()
        body = doc.get('body', {})
        content = body.get('content', [])
        return content[-1].get('endIndex', 1) if content else 1

    def _docs_batch_update_sync(self, doc_id: str, requests: list) -> dict:
        return self.google_docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

    async def docs_update(self, doc_id: str, content: str, update_mode: str = 'APPEND') -> dict:
        """Appends or replaces content in a Google Doc."""
        if not self.google_docs_service:
            raise MCPToolError("Google Docs service not initialized", code=-32603)
        try:
            end_index = await asyncio.to_thread(self._docs_get_end_index_sync, doc_id)
            requests = []
            if update_mode.upper() == 'REPLACE':
                if end_index > 1:
                    requests.append({'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}})
                requests.append({'insertText': {'location': {'index': 1}, 'text': content}})
            else: # APPEND
                # Ensure content starts on a new line if doc is not empty
                insert_text = content
                if end_index > 1:
                     insert_text = '\n' + content
                requests.append({'insertText': {'location': {'index': end_index - 1}, 'text': insert_text}})

            result = await asyncio.to_thread(self._docs_batch_update_sync, doc_id, requests)
            return {"doc_id": doc_id, "replies": len(result.get('replies', [])), "status": "success"}
        except HttpError as e:
            error_msg = f"Google Docs update error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"doc_id": doc_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    async def docs_create_from_markdown(self, title: str, markdown_content: str) -> dict:
        """Creates a new Google Doc from Markdown content."""
        if not self.google_docs_service or not self.google_drive_service:
            raise MCPToolError("Google Docs/Drive services not initialized", code=-32603)
        try:
            # 1. Create a blank document first
            doc_info = await self.docs_create(title)
            doc_id = doc_info['doc_id']

            # 2. Build a list of requests from markdown
            requests = []
            current_index = 1
            lines = markdown_content.split('\n')

            for line in lines:
                line_with_newline = line + '\n'
                line_len = len(line_with_newline)

                # Insert the text of the current line
                requests.append({'insertText': {'location': {'index': current_index}, 'text': line_with_newline}})

                # Apply formatting based on markdown syntax
                range_to_format = {'startIndex': current_index, 'endIndex': current_index + line_len -1}

                if line.startswith('# '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_1'}, 'fields': 'namedStyleType'}})
                elif line.startswith('## '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_2'}, 'fields': 'namedStyleType'}})
                elif line.startswith('### '):
                    requests.append({'updateParagraphStyle': {'range': range_to_format, 'paragraphStyle': {'namedStyleType': 'HEADING_3'}, 'fields': 'namedStyleType'}})
                elif line.strip().startswith(('* ', '- ')):
                    requests.append({'createParagraphBullets': {'range': range_to_format, 'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'}})

                current_index += line_len

            # 3. Send all requests in a single batch update
            if requests:
                await asyncio.to_thread(self._docs_batch_update_sync, doc_id, requests)

            return doc_info
        except HttpError as e:
            error_msg = f"Google Docs markdown creation error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE SLIDES OPERATIONS ============

    def _slides_create_sync(self, title: str) -> dict:
        body = {"title": title}
        return self.google_slides_service.presentations().create(body=body).execute()

    async def slides_create(self, title: str) -> dict:
        """Create a new Google Slides presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating new presentation: {title}", "sergey")

            presentation = await asyncio.to_thread(self._slides_create_sync, title)

            await jlogger.log("INFO", "Successfully created presentation", "sergey", data={"presentation_id": presentation.get("presentationId"), "title": title})
            return {"presentation_id": presentation.get("presentationId"), "title": title, "url": f"https://docs.google.com/presentation/d/{presentation.get('presentationId')}/edit"}
        except HttpError as e:
            error_msg = f"Google Slides create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"title": title, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _slides_add_slide_sync(self, presentation_id: str, title_text: str, body_text: Optional[str]) -> dict:
        slide_id = f"slide_{int(datetime.now().timestamp() * 1000)}"
        requests = [
            {
                "createSlide": {
                    "objectId": slide_id,
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"}
                }
            }
        ]

        # Add title text
        if title_text:
            requests.append({
                "insertText": {
                    "objectId": f"{slide_id}.title",
                    "text": title_text
                }
            })

        # Add body text
        if body_text:
            requests.append({
                "insertText": {
                    "objectId": f"{slide_id}.body",
                    "text": body_text
                }
            })

        body = {"requests": requests}
        return self.google_slides_service.presentations().batchUpdate(
            presentationId=presentation_id, body=body
        ).execute()

    async def slides_add_slide(self, presentation_id: str, title: str, body: Optional[str] = None) -> dict:
        """Add a new slide to a presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Adding slide to presentation {presentation_id}", "sergey")

            result = await asyncio.to_thread(self._slides_add_slide_sync, presentation_id, title, body)

            await jlogger.log("INFO", "Successfully added slide", "sergey")
            return {"presentation_id": presentation_id, "status": "success", "replies_count": len(result.get('replies', []))}
        except HttpError as e:
            error_msg = f"Google Slides add slide error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"presentation_id": presentation_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _slides_read_sync(self, presentation_id: str) -> dict:
        return self.google_slides_service.presentations().get(presentationId=presentation_id).execute()

    async def slides_read(self, presentation_id: str) -> dict:
        """Read information about a presentation."""
        if not self.google_slides_service:
            raise MCPToolError("Google Slides service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Reading presentation {presentation_id}", "sergey")

            presentation = await asyncio.to_thread(self._slides_read_sync, presentation_id)

            slides = presentation.get('slides', [])
            slide_info = []
            for slide in slides:
                slide_data = {"slide_id": slide.get('objectId')}
                # Extract title if exists
                for element in slide.get('pageElements', []):
                    if element.get('shape', {}).get('shapeType') == 'TEXT_BOX':
                        if 'text' in element.get('shape', {}):
                            text_elements = element['shape']['text'].get('textElements', [])
                            text_content = ''.join([t.get('textRun', {}).get('content', '') for t in text_elements if 'textRun' in t])
                            slide_data['content'] = text_content[:100]  # First 100 chars
                slide_info.append(slide_data)

            await jlogger.log("INFO", "Successfully read presentation", "sergey")
            return {
                "presentation_id": presentation_id,
                "title": presentation.get('title'),
                "slide_count": len(slides),
                "slides": slide_info
            }
        except HttpError as e:
            error_msg = f"Google Slides read error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"presentation_id": presentation_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE CALENDAR OPERATIONS ============

    def _calendar_list_sync(self, time_min: Optional[str], time_max: Optional[str], max_results: int) -> dict:
        params = {
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        if time_min:
            params['timeMin'] = time_min
        if time_max:
            params['timeMax'] = time_max

        return self.google_calendar_service.events().list(
            calendarId='primary', **params
        ).execute()

    async def calendar_list_events(self, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> dict:
        """List calendar events."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", "Listing calendar events", "sergey")

            # Default to next 7 days if no time range specified
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            if not time_max:
                time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

            result = await asyncio.to_thread(self._calendar_list_sync, time_min, time_max, max_results)

            events = result.get('items', [])
            event_list = []
            for event in events:
                event_data = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No title'),
                    'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                    'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')[:200] if event.get('description') else ''
                }
                event_list.append(event_data)

            await jlogger.log("INFO", f"Found {len(events)} events", "sergey")
            return {"events": event_list, "count": len(events)}
        except HttpError as e:
            error_msg = f"Google Calendar list error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _calendar_create_sync(self, summary: str, start_time: str, end_time: str, description: Optional[str], location: Optional[str], attendees: Optional[List[str]]) -> dict:
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'}
        }

        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        return self.google_calendar_service.events().insert(
            calendarId='primary', body=event
        ).execute()

    async def calendar_create_event(self, summary: str, start_time: str, end_time: str,
                                   description: Optional[str] = None, location: Optional[str] = None,
                                   attendees: Optional[List[str]] = None) -> dict:
        """Create a calendar event."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating calendar event: {summary}", "sergey")

            event = await asyncio.to_thread(self._calendar_create_sync, summary, start_time, end_time, description, location, attendees)

            await jlogger.log("INFO", "Successfully created event", "sergey", data={"event_id": event.get('id'), "summary": summary})
            return {
                "event_id": event.get('id'),
                "summary": summary,
                "link": event.get('htmlLink'),
                "status": "created"
            }
        except HttpError as e:
            error_msg = f"Google Calendar create error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"summary": summary, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _calendar_delete_sync(self, event_id: str) -> None:
        self.google_calendar_service.events().delete(
            calendarId='primary', eventId=event_id
        ).execute()

    async def calendar_delete_event(self, event_id: str) -> dict:
        """Delete a calendar event."""
        if not self.google_calendar_service:
            raise MCPToolError("Google Calendar service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Deleting calendar event: {event_id}", "sergey")

            await asyncio.to_thread(self._calendar_delete_sync, event_id)

            await jlogger.log("INFO", "Successfully deleted event", "sergey", data={"event_id": event_id})
            return {"event_id": event_id, "status": "deleted"}
        except HttpError as e:
            error_msg = f"Google Calendar delete error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"event_id": event_id, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    # ============ GOOGLE DRIVE OPERATIONS ============

    def _drive_list_sync(self, query: Optional[str], page_size: int) -> dict:
        params = {'pageSize': page_size, 'fields': "nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)"}
        if query:
            params['q'] = query
        return self.google_drive_service.files().list(**params).execute()

    async def drive_list(self, query: Optional[str] = None, page_size: int = 20) -> dict:
        """List files in Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", "Listing Drive files", "sergey", data={"query": query})

            results = await asyncio.to_thread(self._drive_list_sync, query, page_size)

            files = results.get('files', [])
            await jlogger.log("INFO", f"Found {len(files)} files", "sergey")
            return {"files": files, "count": len(files), "next_page_token": results.get('nextPageToken')}
        except HttpError as e:
            error_msg = f"Google Drive list error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"query": query, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _drive_upload_sync(self, file_path: str, folder_id: Optional[str]) -> dict:
        file_name = os.path.basename(file_path)
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        mime_type, _ = mimetypes.guess_type(file_path)
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        return self.google_drive_service.files().create(
            body=file_metadata, media_body=media, fields='id, name, webViewLink'
        ).execute()

    async def drive_upload(self, file_path: str, folder_id: Optional[str] = None) -> dict:
        """Upload a file to Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        if not os.path.exists(file_path):
            raise MCPToolError(f"File not found: {file_path}", code=-32602, data={"file_path": file_path})
        try:
            file_name = os.path.basename(file_path)
            await jlogger.log("INFO", f"Uploading file: {file_name}", "sergey")

            file = await asyncio.to_thread(self._drive_upload_sync, file_path, folder_id)

            await jlogger.log("INFO", "Successfully uploaded file", "sergey", data={"file_id": file['id'], "name": file_name})
            return {"file_id": file['id'], "name": file['name'], "url": file.get('webViewLink')}
        except HttpError as e:
            error_msg = f"Google Drive upload error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"file": file_path, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

    def _drive_create_folder_sync(self, folder_name: str, parent_folder_id: Optional[str]) -> dict:
        file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        return self.google_drive_service.files().create(
            body=file_metadata, fields='id, name, webViewLink'
        ).execute()

    async def drive_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> dict:
        """Create a folder in Google Drive in a non-blocking way."""
        if not self.google_drive_service:
            raise MCPToolError("Google Drive service not initialized", code=-32603)
        try:
            await jlogger.log("INFO", f"Creating folder: {folder_name}", "sergey")

            folder = await asyncio.to_thread(self._drive_create_folder_sync, folder_name, parent_folder_id)

            await jlogger.log("INFO", "Successfully created folder", "sergey", data={"folder_id": folder['id'], "name": folder_name})
            return {"folder_id": folder['id'], "name": folder['name'], "url": folder.get('webViewLink')}
        except HttpError as e:
            error_msg = f"Google Drive folder creation error: {e.reason}"
            await jlogger.log("ERROR", error_msg, "sergey", data={"folder": folder_name, "error": str(e)})
            raise MCPToolError(error_msg, code=e.resp.status)

# Global workspace instance
workspace: Optional[SergeyWorkspace] = None

# ============ MCP TOOL HANDLERS ============
async def sheets_read_handler(sheet_id: str, range: str = "A1:Z1000") -> dict:
    return await workspace.sheets_read(sheet_id, range)

async def sheets_write_handler(sheet_id: str, range: str, values: list) -> dict:
    return await workspace.sheets_write(sheet_id, range, values)

async def sheets_create_handler(title: str) -> dict:
    return await workspace.sheets_create(title)

async def docs_create_handler(title: str, content: Optional[str] = None) -> dict:
    return await workspace.docs_create(title, content)

async def docs_read_handler(doc_id: str) -> dict:
    return await workspace.docs_read(doc_id)

async def docs_update_handler(doc_id: str, content: str, update_mode: str = 'APPEND') -> dict:
    return await workspace.docs_update(doc_id, content, update_mode)

async def docs_create_from_markdown_handler(title: str, markdown_content: str) -> dict:
    return await workspace.docs_create_from_markdown(title, markdown_content)

async def slides_create_handler(title: str) -> dict:
    return await workspace.slides_create(title)

async def slides_add_slide_handler(presentation_id: str, title: str, body: Optional[str] = None) -> dict:
    return await workspace.slides_add_slide(presentation_id, title, body)

async def slides_read_handler(presentation_id: str) -> dict:
    return await workspace.slides_read(presentation_id)

async def calendar_list_events_handler(time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 10) -> dict:
    return await workspace.calendar_list_events(time_min, time_max, max_results)

async def calendar_create_event_handler(summary: str, start_time: str, end_time: str,
                                       description: Optional[str] = None, location: Optional[str] = None,
                                       attendees: Optional[List[str]] = None) -> dict:
    return await workspace.calendar_create_event(summary, start_time, end_time, description, location, attendees)

async def calendar_delete_event_handler(event_id: str) -> dict:
    return await workspace.calendar_delete_event(event_id)

async def drive_list_handler(query: Optional[str] = None, page_size: int = 20) -> dict:
    return await workspace.drive_list(query, page_size)

async def drive_upload_handler(file_path: str, folder_id: Optional[str] = None) -> dict:
    return await workspace.drive_upload(file_path, folder_id)

async def drive_create_folder_handler(name: str, parent_id: Optional[str] = None) -> dict:
    return await workspace.drive_create_folder(name, parent_id)

# ============ MCP TOOL DEFINITIONS ============
TOOLS = {
    # Sheets
    "sergey_sheets_read": {"description": "Read data from a Google Sheet.", "inputSchema": {"type": "object", "properties": {"sheet_id": {"type": "string", "description": "Google Sheet ID"}, "range": {"type": "string", "description": "Range to read (e.g., 'Sheet1!A1:B10')", "default": "A1:Z1000"}}, "required": ["sheet_id"]}},
    "sergey_sheets_write": {"description": "Write data to a Google Sheet.", "inputSchema": {"type": "object", "properties": {"sheet_id": {"type": "string", "description": "Google Sheet ID"}, "range": {"type": "string", "description": "Range to write (e.g., 'Sheet1!A1')"}, "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}, "description": "2D array of values to write."}}, "required": ["sheet_id", "range", "values"]}},
    "sergey_sheets_create": {"description": "Create a new Google Sheet.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new sheet."}}, "required": ["title"]}},
    # Docs
    "sergey_docs_create": {"description": "Create a new Google Document.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new document."}, "content": {"type": "string", "description": "Initial plain text content for the document."}}, "required": ["title"]}},
    "sergey_docs_read": {"description": "Read all text content from a Google Document.", "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string", "description": "Google Document ID"}}, "required": ["doc_id"]}},
    "sergey_docs_update": {"description": "Append or replace content in an existing Google Document.", "inputSchema": {"type": "object", "properties": {"doc_id": {"type": "string", "description": "ID of the document to update."}, "content": {"type": "string", "description": "The text content to add."}, "update_mode": {"type": "string", "description": "How to update: 'APPEND' or 'REPLACE'.", "enum": ["APPEND", "REPLACE"], "default": "APPEND"}}, "required": ["doc_id", "content"]}},
    "sergey_docs_create_from_markdown": {"description": "Create a new Google Document from Markdown content, preserving basic formatting.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new document."}, "markdown_content": {"type": "string", "description": "The document content in Markdown format. Supports headings (#, ##) and bullet points (* or -)."}}, "required": ["title", "markdown_content"]}},
    # Slides
    "sergey_slides_create": {"description": "Create a new Google Slides presentation.", "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "description": "Title for the new presentation."}}, "required": ["title"]}},
    "sergey_slides_add_slide": {"description": "Add a new slide to an existing presentation.", "inputSchema": {"type": "object", "properties": {"presentation_id": {"type": "string", "description": "ID of the presentation."}, "title": {"type": "string", "description": "Title text for the slide."}, "body": {"type": "string", "description": "Body text for the slide (optional)."}}, "required": ["presentation_id", "title"]}},
    "sergey_slides_read": {"description": "Get information about a Google Slides presentation.", "inputSchema": {"type": "object", "properties": {"presentation_id": {"type": "string", "description": "ID of the presentation to read."}}, "required": ["presentation_id"]}},
    # Calendar
    "sergey_calendar_list_events": {"description": "List calendar events within a time range.", "inputSchema": {"type": "object", "properties": {"time_min": {"type": "string", "description": "Start time in ISO format (e.g., '2024-01-01T00:00:00Z')."}, "time_max": {"type": "string", "description": "End time in ISO format."}, "max_results": {"type": "integer", "description": "Maximum number of events to return.", "default": 10}}}},
    "sergey_calendar_create_event": {"description": "Create a new calendar event.", "inputSchema": {"type": "object", "properties": {"summary": {"type": "string", "description": "Event title/summary."}, "start_time": {"type": "string", "description": "Start time in ISO format (e.g., '2024-01-01T10:00:00Z')."}, "end_time": {"type": "string", "description": "End time in ISO format."}, "description": {"type": "string", "description": "Event description (optional)."}, "location": {"type": "string", "description": "Event location (optional)."}, "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses (optional)."}}, "required": ["summary", "start_time", "end_time"]}},
    "sergey_calendar_delete_event": {"description": "Delete a calendar event.", "inputSchema": {"type": "object", "properties": {"event_id": {"type": "string", "description": "ID of the event to delete."}}, "required": ["event_id"]}},
    # Drive
    "sergey_drive_list": {"description": "List files in Google Drive, optionally with a search query.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query in Drive API format (e.g., \"name contains 'report' and mimeType='application/vnd.google-apps.spreadsheet'\")."}, "page_size": {"type": "integer", "description": "Number of results to return.", "default": 20}}}},
    "sergey_drive_upload": {"description": "Upload a local file to Google Drive.", "inputSchema": {"type": "object", "properties": {"file_path": {"type": "string", "description": "Absolute path to the local file to upload."}, "folder_id": {"type": "string", "description": "ID of the parent folder in Google Drive (optional)."}}, "required": ["file_path"]}},
    "sergey_drive_create_folder": {"description": "Create a new folder in Google Drive.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "description": "Name for the new folder."}, "parent_id": {"type": "string", "description": "ID of the parent folder (optional)."}}, "required": ["name"]}},
}

# ============ MCP TOOL HANDLERS MAPPING ============
HANDLERS = {
    "sergey_sheets_read": sheets_read_handler,
    "sergey_sheets_write": sheets_write_handler,
    "sergey_sheets_create": sheets_create_handler,
    "sergey_docs_create": docs_create_handler,
    "sergey_docs_read": docs_read_handler,
    "sergey_docs_update": docs_update_handler,
    "sergey_docs_create_from_markdown": docs_create_from_markdown_handler,
    "sergey_slides_create": slides_create_handler,
    "sergey_slides_add_slide": slides_add_slide_handler,
    "sergey_slides_read": slides_read_handler,
    "sergey_calendar_list_events": calendar_list_events_handler,
    "sergey_calendar_create_event": calendar_create_event_handler,
    "sergey_calendar_delete_event": calendar_delete_event_handler,
    "sergey_drive_list": drive_list_handler,
    "sergey_drive_upload": drive_upload_handler,
    "sergey_drive_create_folder": drive_create_folder_handler,
}

# ============ MAIN ENTRY POINT ============
async def main():
    """Main entry point for Sergey MAD"""
    global workspace

    port = int(os.getenv("SERGEY_PORT", "8095"))
    service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "/config/google-service-account-credentials.json")

    if not os.path.exists(service_account_path):
        msg = f"FATAL: Google service account file not found at {service_account_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    workspace = SergeyWorkspace(service_account_path)
    await workspace.initialize()

    server = MCPServer(
        name="sergey",
        version="2.0.0", # Version bumped to reflect full Google Workspace suite
        port=port,
        tool_definitions=TOOLS,
        tool_handlers=HANDLERS
    )

    logger.info(f"Starting Sergey MAD on port {port} with {len(TOOLS)} tools registered.")
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (FileNotFoundError, KeyboardInterrupt) as e:
        logger.info(f"Sergey server shutting down: {e}")
    except Exception as e:
        logger.critical("An unhandled exception occurred in Sergey MAD", exc_info=True)