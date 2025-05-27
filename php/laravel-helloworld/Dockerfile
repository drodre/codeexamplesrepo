# Use an official PHP image with Apache
FROM php:8.1-apache

# Set working directory
WORKDIR /var/www/html

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    zip \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install PHP extensions required by Laravel
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Install Composer globally
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Copy application source code
COPY . .

# Copy Apache virtual host configuration (optional, but good practice)
# If you have a custom vhost, copy it here. For now, default should work.
# COPY 000-default.conf /etc/apache2/sites-available/000-default.conf

# Set permissions for storage and bootstrap/cache
RUN chown -R www-data:www-data storage bootstrap/cache
RUN chmod -R 775 storage bootstrap/cache

# Install Composer dependencies
RUN composer install --optimize-autoloader --no-dev --no-interaction --no-plugins --no-scripts

# Generate application key (important for Laravel) - this will use the .env.example if .env is not present
# It's better to have APP_KEY set in the .env file during build or runtime.
# RUN php artisan key:generate --force

# Expose port 80
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]
