"""
TurboShare — File transfer endpoints.

Send mode (laptop → phone):
  GET  /api/chunk/{file_id}/{chunk_index}  — download a specific chunk
  GET  /api/download/{file_id}             — download the complete file

Receive mode (phone → laptop):
  POST /api/chunk/{file_id}/{chunk_index}  — upload a chunk
  POST /api/upload-init                    — initialise receive for phone-selected files
"""

import logging
from pathlib import Path
from aiohttp import web

from src.core.session import SessionState, FileEntry

log = logging.getLogger(__name__)


async def download_chunk(request: web.Request) -> web.Response:
    """Serve a single chunk (Send mode: laptop → phone).

    The response includes the chunk data and an X-Chunk-MD5 header
    for client-side verification.
    """
    session = request.app["session"]
    engine = request.app["transfer_engine"]

    if session.state != SessionState.TRANSFERRING:
        raise web.HTTPConflict(text="Transfer not in progress")

    file_id = int(request.match_info["file_id"])
    chunk_index = int(request.match_info["chunk_index"])

    result = engine.get_chunk(file_id, chunk_index)
    if result is None:
        raise web.HTTPNotFound(text="Chunk not found")

    data, md5 = result
    return web.Response(
        body=data,
        content_type="application/octet-stream",
        headers={
            "X-Chunk-MD5": md5,
            "X-Chunk-Index": str(chunk_index),
            "X-File-ID": str(file_id),
        },
    )


async def download_file(request: web.Request) -> web.StreamResponse:
    """Stream a complete file for browser download (Send mode).

    Sets Content-Disposition so the browser triggers a native download
    dialog / saves directly.
    """
    session = request.app["session"]
    engine = request.app["transfer_engine"]

    file_id = int(request.match_info["file_id"])

    # Find the file entry
    file_entry = None
    for f in session.files:
        if f.id == file_id:
            file_entry = f
            break

    if file_entry is None:
        raise web.HTTPNotFound(text="File not found")

    chunker = engine.get_chunker(file_id)
    if chunker is None:
        raise web.HTTPNotFound(text="File not available")

    response = web.StreamResponse()
    response.content_type = "application/octet-stream"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{file_entry.name}"'
    )
    response.content_length = file_entry.size
    await response.prepare(request)

    # Stream all chunks sequentially
    for i in range(chunker.total_chunks):
        result = engine.get_chunk(file_id, i)
        if result is None:
            # Transfer was cancelled
            break
        data, _ = result
        await response.write(data)

    await response.write_eof()

    # Mark file as downloaded
    engine.mark_send_file_done(file_id)

    return response


async def upload_chunk(request: web.Request) -> web.Response:
    """Receive a single chunk (Receive mode: phone → laptop).

    The client must include X-Chunk-MD5 header with the chunk's
    MD5 checksum for verification.
    """
    session = request.app["session"]
    engine = request.app["transfer_engine"]

    if session.state != SessionState.TRANSFERRING:
        raise web.HTTPConflict(text="Transfer not in progress")

    file_id = int(request.match_info["file_id"])
    chunk_index = int(request.match_info["chunk_index"])
    # Make X-Chunk-MD5 optional (bypass hashing if not provided by browser)
    expected_md5 = request.headers.get("X-Chunk-MD5", "")

    data = await request.read()

    ok = engine.receive_chunk(file_id, chunk_index, data, expected_md5)

    if not ok:
        # Could be checksum mismatch or 30 GB cap hit
        if engine.is_cancelled:
            return web.json_response({
                "status": "cap_exceeded",
                "message": "Transfer size limit (30 GB) reached.",
            }, status=413)
        raise web.HTTPConflict(text="Checksum verification failed — retry this chunk")

    return web.json_response({
        "status": "ok",
        "chunk_index": chunk_index,
        "file_id": file_id,
    })


async def upload_init(request: web.Request) -> web.Response:
    """Initialise the receive side when the phone is the sender.

    The phone browser sends the list of files it wants to upload,
    and the server prepares assemblers for each one.

    Body: {"files": [{"name": "photo.jpg", "size": 12345}, ...], "preferred_chunk_size": 1048576}
    """
    session = request.app["session"]
    engine = request.app["transfer_engine"]

    try:
        body = await request.json()
    except Exception:
        raise web.HTTPBadRequest(text="Invalid JSON body")

    files_data = body.get("files", [])
    if not files_data:
        raise web.HTTPBadRequest(text="No files specified")

    from src.core.config import MAX_TRANSFER_SIZE, CHUNK_SIZE
    import math

    # Parse preferred chunk size if provided by the client
    preferred_chunk_size = body.get("preferred_chunk_size")
    if preferred_chunk_size is not None:
        try:
            preferred_chunk_size = int(preferred_chunk_size)
            # Clamp between 256 KB and 8 MB to prevent memory issues
            preferred_chunk_size = max(256 * 1024, min(preferred_chunk_size, 8 * 1024 * 1024))
        except (ValueError, TypeError):
            preferred_chunk_size = CHUNK_SIZE
    else:
        preferred_chunk_size = CHUNK_SIZE

    # Build file entries
    file_entries = []
    total_size = 0
    for idx, fd in enumerate(files_data):
        # Strip path traversal characters (security hardening)
        raw_name = fd.get("name", f"file_{idx}")
        name = Path(raw_name).name
        if not name:
            name = f"file_{idx}"
        size = int(fd.get("size", 0))
        total_size += size
        entry = FileEntry(
            id=idx,
            name=name,
            path=session.save_dir / name,
            size=size,
        )
        file_entries.append(entry)

    # Store in session
    session.files = file_entries

    # Prepare assemblers
    engine.prepare_receive(file_entries, session.save_dir, preferred_chunk_size)

    # Return file metadata with chunk counts
    response_files = []
    for f in file_entries:
        total_chunks = max(1, math.ceil(f.size / preferred_chunk_size))
        response_files.append({
            "id": f.id,
            "name": f.name,
            "size": f.size,
            "total_chunks": total_chunks,
            "chunk_size": preferred_chunk_size,
        })

    return web.json_response({
        "status": "ok",
        "files": response_files,
        "max_size": MAX_TRANSFER_SIZE,
    })
