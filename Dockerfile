FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DISPLAY=:99
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    xvfb x11vnc openbox novnc websockify && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir playwright==1.56.0
WORKDIR /workspace
COPY extractor/*.py /workspace/extractor/
COPY --chmod=755 extractor/entrypoint-agent.sh /workspace/extractor/entrypoint-agent.sh
RUN mkdir -p /data/browser /data/state && chown -R pwuser:pwuser /data
USER pwuser
ENV HOME=/data/browser BROWSER_PROFILE=/data/browser STATE_FILE=/data/state/attempts.json
EXPOSE 6080 8787
ENTRYPOINT ["/bin/sh", "/workspace/extractor/entrypoint-agent.sh"]
