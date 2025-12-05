FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app with increased memory
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# Install serve globally
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the built app
CMD serve dist -l ${PORT:-3000}
