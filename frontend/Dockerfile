FROM oven/bun:1 AS base

WORKDIR /app

# Copy package files first for better layer caching.
COPY package.json bun.lock* ./

RUN bun install --frozen-lockfile

FROM base AS development

COPY . .

EXPOSE 5173

CMD ["bun", "run", "dev", "--", "--host", "0.0.0.0"]

FROM base AS build

COPY . .

RUN bun run build

FROM oven/bun:1 AS production

WORKDIR /app

COPY --from=build /app/dist ./dist

RUN bun add -g serve

EXPOSE 3000

CMD ["serve", "dist", "-l", "3000"]
