import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from config import Config
from flask_migrate import Migrate
from extensions import db, migrate
from models import Asset, AssetFile

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure the uploads folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize database
    #with app.app_context():
    #    db.create_all()

    return app

app = create_app()

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    # Get the file extension
    ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
    # Generate a unique filename using UUID
    return f"{uuid.uuid4().hex}{ext}"

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip', 'spp', 'unitypackage', 'fbx', 'blend', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_file(filename):
    if filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/')
def index():
    assets = Asset.query.order_by(Asset.created_at.desc()).all()
    return render_template('index.html', assets=assets)

@app.route('/asset/add', methods=['GET', 'POST'])
def add_asset():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        license_key = request.form.get('license_key')
        featured_image = request.files.get('featured_image')
        additional_files = request.files.getlist('additional_files')

        if title and featured_image and allowed_file(featured_image.filename):
            # Generate unique filename for featured image
            original_featured_filename = secure_filename(featured_image.filename)
            unique_featured_filename = generate_unique_filename(original_featured_filename)

            # Save featured image with unique filename
            featured_image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_featured_filename))

            # Create asset with unique filename
            asset = Asset(
                title=title,
                featured_image=unique_featured_filename,
                original_featured_image=original_featured_filename,
                license_key=license_key.strip() if license_key else None
            )
            asset.set_description(description)
            db.session.add(asset)
            db.session.commit()

            # Save additional files with unique filenames
            for file in additional_files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    unique_filename = generate_unique_filename(original_filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    asset_file = AssetFile(
                        filename=unique_filename,
                        original_filename=original_filename,
                        asset_id=asset.id
                    )
                    db.session.add(asset_file)

            db.session.commit()
            flash('Asset added successfully!', 'success')
            return redirect(url_for('index'))

    return render_template('add_asset.html')

@app.route('/asset/<int:id>')
def asset_detail(id):
    asset = Asset.query.get_or_404(id)
    return render_template('asset_detail.html', asset=asset)

@app.route('/asset/<int:id>/edit', methods=['GET', 'POST'])
def edit_asset(id):
    asset = Asset.query.get_or_404(id)

    if request.method == 'POST':
        asset.title = request.form.get('title')
        asset.set_description(request.form.get('description'))
        license_key = request.form.get('license_key')
        asset.license_key = license_key.strip() if license_key else None

        # Handle featured image update
        featured_image = request.files.get('featured_image')
        if featured_image and featured_image.filename and allowed_file(featured_image.filename):
            # Delete old featured image
            delete_file(asset.featured_image)

            # Save new featured image
            original_featured_filename = secure_filename(featured_image.filename)
            unique_featured_filename = generate_unique_filename(original_featured_filename)
            # Save featured image with unique filename
            featured_image.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_featured_filename))
            asset.featured_image = unique_featured_filename

        # Handle additional files
        additional_files = request.files.getlist('additional_files')
        for file in additional_files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                unique_filename = generate_unique_filename(original_filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                asset_file = AssetFile(
                    filename=unique_filename,
                    original_filename=original_filename,
                    asset_id=asset.id
                )
                db.session.add(asset_file)

        db.session.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('asset_detail', id=asset.id))

    return render_template('edit_asset.html', asset=asset)

@app.route('/asset/<int:id>/delete', methods=['POST'])
def delete_asset(id):
    asset = Asset.query.get_or_404(id)

    # Delete featured image
    delete_file(asset.featured_image)

    # Delete additional files
    for file in asset.files:
        delete_file(file.filename)
        db.session.delete(file)

    db.session.delete(asset)
    db.session.commit()

    flash('Asset deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/asset/file/<int:id>/delete', methods=['POST'])
def delete_asset_file(id):
    asset_file = AssetFile.query.get_or_404(id)
    asset_id = asset_file.asset_id

    # Delete the file
    delete_file(asset_file.filename)

    # Remove from database
    db.session.delete(asset_file)
    db.session.commit()

    flash('File deleted successfully!', 'success')
    return redirect(url_for('asset_detail', id=asset_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
