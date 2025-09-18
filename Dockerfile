FROM amrit3701/freecad-cli:0.21-amd64-01.05.2024

# 1. Update apt repositories to the old-releases archive.
RUN sed -i 's|http://archive.ubuntu.com|http://old-releases.ubuntu.com|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com|http://old-releases.ubuntu.com|g' /etc/apt/sources.list

# 2. Install wget, which is needed for the download.
RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/*

# --- FINAL FIX for FBX2glTF Download ---
# 3. Download the executable directly and make it runnable.
RUN wget https://github.com/facebookincubator/FBX2glTF/releases/download/v0.9.7/FBX2glTF-linux-x64 -O /usr/local/bin/FBX2glTF && \
    chmod +x /usr/local/bin/FBX2glTF

# Set the working directory inside the container
WORKDIR /app

# Copy the project definition file and source code
COPY pyproject.toml .
COPY ./src/ /app/src/

# Install our project and its dependencies
RUN pip3 install --no-cache-dir "." --break-system-packages

# The command to run the application will be specified in docker-compose.yml
# EXPOSE 8000