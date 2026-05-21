# stock-mcp -- MCP server container.
# Single-stage: all deps install from manylinux wheels, no build toolchain needed.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 39200

CMD ["stock-mcp"]
