from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'  # Necesario para los mensajes flash

# Configurar la URI de la base de datos MySQL (con XAMPP, el usuario es 'root' y no tiene contraseña)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/spotify'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Crear la instancia de SQLAlchemy
db = SQLAlchemy(app)

# Definir el modelo de la base de datos para las canciones (según la tabla 'musica')
class Musica(db.Model):
    __tablename__ = 'musica'  # Asegúrate de que la tabla sea 'musica'
    id = db.Column(db.Integer, primary_key=True)
    cancion = db.Column(db.String(100), nullable=True)
    artista = db.Column(db.String(100), nullable=True)
    album = db.Column(db.String(100), nullable=True)
    anio = db.Column(db.Integer, nullable=True)
    duracion = db.Column(db.Integer, nullable=True)
    fecha_lanzamiento = db.Column(db.Date, nullable=True)
    hora_estreno = db.Column(db.Time, nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    email_contacto = db.Column(db.String(100), nullable=True)
    activo = db.Column(db.Boolean, default=True)

# Definir el modelo de la base de datos para las playlists
playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('musica_id', db.Integer, db.ForeignKey('musica.id'))
)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    canciones = db.relationship('Musica', secondary=playlist_song, backref='playlists')

# Ruta principal de la aplicación (Listado de canciones y filtros)
@app.route('/', methods=['GET', 'POST'])
def index():
    musica = Musica.query.filter(Musica.activo == True).all()  # Obtener todas las canciones activas
    playlists = Playlist.query.all()  # Obtener todas las playlists
    
    if request.method == 'POST':
        cancion = request.form['cancion']
        artista = request.form['artista']
        album = request.form['album']
        anio = request.form['anio']
        duracion = request.form['duracion']
        descripcion = request.form['descripcion']
        email_contacto = request.form['email_contacto']

        nueva_cancion = Musica(
            cancion=cancion,
            artista=artista,
            album=album,
            anio=anio,
            duracion=duracion,
            descripcion=descripcion,
            email_contacto=email_contacto
        )

        db.session.add(nueva_cancion)
        db.session.commit()
        flash(f'La canción "{nueva_cancion.cancion}" ha sido agregada correctamente.', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', songs=musica, playlists=playlists)

# Caso 2 - Baja lógica de música (Desactivar canción)
@app.route('/delete_song/<int:id>', methods=['GET'])
def delete_song(id):
    musica = Musica.query.get_or_404(id)
    musica.activo = False  # Baja lógica
    db.session.commit()
    flash(f'La canción "{musica.cancion}" ha sido desactivada.', 'warning')
    return redirect(url_for('index'))

# Caso 3 - Crear y editar canciones
@app.route('/edit_song/<int:id>', methods=['GET', 'POST'])
def edit_song(id):
    musica = Musica.query.get_or_404(id)

    if request.method == 'POST':
        musica.cancion = request.form['cancion']
        musica.artista = request.form['artista']
        musica.album = request.form['album']
        musica.anio = request.form['anio']
        musica.duracion = request.form['duracion']
        musica.descripcion = request.form['descripcion']
        musica.email_contacto = request.form['email_contacto']
        
        db.session.commit()
        flash(f'La canción "{musica.cancion}" ha sido actualizada correctamente.', 'success')
        return redirect(url_for('index'))

    return render_template('edit_song.html', musica=musica)

# Caso 4 - Gestión de Playlists (Crear y Agregar canciones)
@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    nombre = request.form['nombre']
    nueva_playlist = Playlist(nombre=nombre)
    db.session.add(nueva_playlist)
    db.session.commit()
    flash(f'La playlist "{nueva_playlist.nombre}" ha sido creada correctamente.', 'success')
    return redirect(url_for('index'))

@app.route('/add_to_playlist/<int:playlist_id>/<int:song_id>')
def add_to_playlist(playlist_id, song_id):
    playlist = Playlist.query.get(playlist_id)
    song = Musica.query.get(song_id)
    
    if playlist and song:
        if song not in playlist.canciones:
            playlist.canciones.append(song)
            db.session.commit()
            flash(f'La canción "{song.cancion}" ha sido agregada a la playlist "{playlist.nombre}".', 'success')
        else:
            flash(f'La canción "{song.cancion}" ya está en la playlist "{playlist.nombre}".', 'warning')
    return redirect(url_for('index'))

# Caso 6 - Eliminar canción de una playlist
@app.route('/remove_from_playlist/<int:playlist_id>/<int:song_id>', methods=['GET'])
def remove_from_playlist(playlist_id, song_id):
    playlist = Playlist.query.get_or_404(playlist_id)  # Obtener la playlist
    song = Musica.query.get_or_404(song_id)  # Obtener la canción

    if song in playlist.canciones:
        playlist.canciones.remove(song)  # Eliminar la canción de la playlist
        db.session.commit()  # Guardar cambios en la base de datos
        flash(f'La canción "{song.cancion}" ha sido eliminada de la playlist "{playlist.nombre}".', 'success')
    else:
        flash('La canción no está en esta playlist.', 'warning')

    return redirect(url_for('playlist_detail', id=playlist_id))  # Redirigir a la página de la playlist

# Caso 5 - Reproducción simulada
@app.route('/play/<int:id>', methods=['GET'])
def play_song(id):
    song = Musica.query.get(id)
    return render_template('player.html', current_song=song)

# Ver canciones dentro de una playlist
@app.route('/playlist/<int:id>', methods=['GET'])
def playlist_detail(id):
    playlist = Playlist.query.get_or_404(id)
    return render_template('playlist_detail.html', playlist=playlist)

# Caso 1 - Filtros de música
@app.route('/songs', methods=['GET'])
def list_songs():
    artist = request.args.get('artist')  # Obtener el artista filtrado
    title = request.args.get('title')  # Obtener el título filtrado

    query = Musica.query.filter(Musica.activo == True)  # Filtrar canciones activas

    if artist:
        query = query.filter(Musica.artista.ilike(f'%{artist}%'))  # Filtrar por artista

    if title:
        query = query.filter(Musica.cancion.ilike(f'%{title}%'))  # Filtrar por título

    musica = query.all()  # Obtener canciones filtradas
    playlists = Playlist.query.all()  # Obtener todas las playlists
    return render_template('index.html', songs=musica, playlists=playlists, artist=artist, title=title)

if __name__ == "__main__":
    app.run(debug=True)
