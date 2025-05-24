import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from config import Config
from flask_migrate import Migrate
from extensions import db, migrate
from models import Asset, AssetFile
from storage import StorageBackend
from image_processor import ImageProcessor
from werkzeug.datastructures import FileStorage

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    return app

app = create_app()
storage = StorageBackend(app.config['STORAGE_URL'])

def generate_unique_filename(original_filename):
    # Get the file extension
    ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
    # Generate a unique filename using UUID
    return f"{uuid.uuid4().hex}{ext}"

def allowed_file(filename, is_featured_image=False):
    if is_featured_image:
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    else:
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip', 'spp', 'unitypackage', 'fbx', 'blend', 'webp', 'tgz', 'tar.gz', '7z'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    assets = Asset.query.order_by(Asset.created_at.desc()).all()
    return render_template('index.html', assets=assets)

@app.route('/asset/add', methods=['GET', 'POST'])
def add_asset():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            license_key = request.form.get('license_key')
            featured_image = request.files.get('featured_image')
            additional_files = request.files.getlist('additional_files')

            if not title:
                return jsonify({'success': False, 'error': 'Title is required'})
            
            if not featured_image:
                return jsonify({'success': False, 'error': 'Featured image is required'})
            
            if not allowed_file(featured_image.filename, is_featured_image=True):
                return jsonify({'success': False, 'error': 'Invalid featured image format'})

            # Process and convert featured image to WebP
            processed_image, ext = ImageProcessor.process_featured_image(featured_image)
            
            # Generate unique filename for featured image
            original_featured_filename = secure_filename(featured_image.filename)
            unique_featured_filename = f"{uuid.uuid4().hex}{ext}"

            # Create a FileStorage object from the processed image
            processed_file = FileStorage(
                stream=processed_image,
                filename=unique_featured_filename,
                content_type='image/webp'
            )

            # Save featured image with unique filename using storage backend
            storage.save(processed_file, unique_featured_filename)

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
                    storage.save(file, unique_filename)
                    asset_file = AssetFile(
                        filename=unique_filename,
                        original_filename=original_filename,
                        asset_id=asset.id
                    )
                    db.session.add(asset_file)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Asset added successfully!',
                'redirect': url_for('index')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            })

    return render_template('add_asset.html')

@app.route('/asset/<int:id>')
def asset_detail(id):
    asset = Asset.query.get_or_404(id)
    return render_template('asset_detail.html', asset=asset)

@app.route('/asset/<int:id>/edit', methods=['GET', 'POST'])
def edit_asset(id):
    asset = Asset.query.get_or_404(id)

    if request.method == 'POST':
        try:
            asset.title = request.form.get('title')
            if not asset.title:
                return jsonify({'success': False, 'error': 'Title is required'})

            asset.set_description(request.form.get('description'))
            license_key = request.form.get('license_key')
            asset.license_key = license_key.strip() if license_key else None

            # Handle featured image update
            featured_image = request.files.get('featured_image')
            if featured_image and featured_image.filename:
                if not allowed_file(featured_image.filename, is_featured_image=True):
                    return jsonify({'success': False, 'error': 'Invalid featured image format'})

                # Delete old featured image
                if asset.featured_image:
                    storage.delete(asset.featured_image)

                # Process and convert featured image to WebP
                processed_image, ext = ImageProcessor.process_featured_image(featured_image)
                
                # Generate unique filename
                original_featured_filename = secure_filename(featured_image.filename)
                unique_featured_filename = f"{uuid.uuid4().hex}{ext}"

                # Create a FileStorage object from the processed image
                processed_file = FileStorage(
                    stream=processed_image,
                    filename=unique_featured_filename,
                    content_type='image/webp'
                )

                # Save the processed image
                storage.save(processed_file, unique_featured_filename)
                asset.featured_image = unique_featured_filename
                asset.original_featured_image = original_featured_filename

            # Handle additional files
            additional_files = request.files.getlist('additional_files')
            for file in additional_files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    unique_filename = generate_unique_filename(original_filename)
                    storage.save(file, unique_filename)
                    asset_file = AssetFile(
                        filename=unique_filename,
                        original_filename=original_filename,
                        asset_id=asset.id
                    )
                    db.session.add(asset_file)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Asset updated successfully!',
                'redirect': url_for('asset_detail', id=asset.id)
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            })

    return render_template('edit_asset.html', asset=asset)

@app.route('/asset/<int:id>/delete', methods=['POST'])
def delete_asset(id):
    try:
        asset = Asset.query.get_or_404(id)
        deletion_errors = []

        # Delete featured image
        if asset.featured_image:
            if not storage.delete(asset.featured_image):
                deletion_errors.append(f"Failed to delete featured image: {asset.featured_image}")

        # Delete additional files
        for file in asset.files:
            if not storage.delete(file.filename):
                deletion_errors.append(f"Failed to delete file: {file.filename}")
            db.session.delete(file)

        db.session.delete(asset)
        db.session.commit()

        if deletion_errors:
            app.logger.error("Asset deletion had errors: %s", deletion_errors)
            flash('Asset deleted from database, but some files could not be deleted: ' + '; '.join(deletion_errors), 'warning')
        else:
            flash('Asset deleted successfully!', 'success')

        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        app.logger.error("Failed to delete asset: %s", str(e))
        flash('Failed to delete asset: ' + str(e), 'error')
        return redirect(url_for('asset_detail', id=id))

@app.route('/asset/file/<int:id>/delete', methods=['POST'])
def delete_asset_file(id):
    try:
        asset_file = AssetFile.query.get_or_404(id)
        asset_id = asset_file.asset_id
        filename = asset_file.filename
        display_name = asset_file.original_filename or asset_file.filename

        # Delete the file using storage backend
        if not storage.delete(filename):
            error_msg = f'Failed to delete file {display_name} from storage'
            app.logger.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('asset_detail', id=asset_id))

        # Only remove from database if storage deletion was successful
        db.session.delete(asset_file)
        db.session.commit()

        flash('File deleted successfully!', 'success')
        return redirect(url_for('asset_detail', id=asset_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error("Failed to delete asset file: %s", str(e))
        flash('Failed to delete file: ' + str(e), 'error')
        return redirect(url_for('asset_detail', id=asset_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5432, debug=True)
