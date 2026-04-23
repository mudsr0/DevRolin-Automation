FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy all frontend code and build the app
COPY . .
# You can pass VITE_API_BASE_URL as an ARG if your backend is hosted remotely
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Use Nginx to serve the static frontend
FROM nginx:alpine
# Copy built files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Add custom Nginx configuration if needed for React Router SPA
# (By default nginx will try to map URLs, so React Router needs try_files fallback if there are many pages)
RUN echo "server { listen 80; location / { root /usr/share/nginx/html; index index.html; try_files \$uri \$uri/ /index.html; } }" > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
