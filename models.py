from datetime import datetime
from extensions import db
import bleach
from flask import current_app

ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
    'strong', 'ul', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span',
    'br', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'img'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
}

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    featured_image = db.Column(db.String(200))
    original_featured_image = db.Column(db.String(200))
    license_key = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('AssetFile', backref='asset', lazy=True)

    def set_description(self, description):
        """Sanitize HTML content before saving"""
        if description:
            clean_html = bleach.clean(
                description,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            self.description = clean_html
        else:
            self.description = None

    @property
    def safe_description(self):
        """Return sanitized HTML content"""
        if self.description:
            return bleach.clean(
                self.description,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
        return ''
    
    @property
    def featured_image_url(self):
        """Get the URL for the featured image"""
        from storage import StorageBackend
        if self.featured_image:
            storage = StorageBackend(current_app.config['STORAGE_URL'])
            return storage.url_for(self.featured_image)
        return None

class AssetFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200))
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)

    @property
    def file_url(self):
        """Get the URL for the file"""
        from storage import StorageBackend
        storage = StorageBackend(current_app.config['STORAGE_URL'])
        return storage.url_for(self.filename)
