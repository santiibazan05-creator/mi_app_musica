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
(app.py)

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mi App de Música</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

<div class="container mt-5">
    <h1 class="text-center">Lista de Canciones</h1>

    <!-- Filtros de búsqueda -->
    <div class="mb-3">
        <form method="GET" action="/songs">
            <label for="artist">Artista:</label>
            <input type="text" id="artist" name="artist" class="form-control" placeholder="Filtrar por artista" value="{{ artist if artist else '' }}">
            
            <label for="title" class="mt-2">Título:</label>
            <input type="text" id="title" name="title" class="form-control" placeholder="Filtrar por título" value="{{ title if title else '' }}">
            
            <button type="submit" class="btn btn-primary mt-2">Filtrar</button>
        </form>
    </div>

    <!-- Formulario para agregar una nueva canción -->
    <h2 class="text-center mb-4">Agregar una nueva canción</h2>
    <form action="/" method="POST" class="border p-4 rounded shadow">
        <div class="form-group">
            <label for="cancion">Canción:</label>
            <input type="text" id="cancion" name="cancion" class="form-control" required><br><br>
        </div>

        <div class="form-group">
            <label for="artista">Artista:</label>
            <input type="text" id="artista" name="artista" class="form-control" required><br><br>
        </div>

        <div class="form-group">
            <label for="album">Álbum:</label>
            <input type="text" id="album" name="album" class="form-control" required><br><br>
        </div>

        <div class="form-group">
            <label for="anio">Año:</label>
            <input type="number" id="anio" name="anio" class="form-control" required><br><br>
        </div>

        <div class="form-group">
            <label for="duracion">Duración (en segundos):</label>
            <input type="number" id="duracion" name="duracion" class="form-control" required><br><br>
        </div>

        <div class="form-group">
            <label for="descripcion">Descripción:</label>
            <textarea id="descripcion" name="descripcion" class="form-control" required></textarea><br><br>
        </div>

        <div class="form-group">
            <label for="email_contacto">Email de contacto:</label>
            <input type="email" id="email_contacto" name="email_contacto" class="form-control" required><br><br>
        </div>

        <button type="submit" class="btn btn-success btn-block">Agregar Canción</button>
    </form>

    <!-- Lista de Canciones -->
    <h2 class="text-center mb-4">Canciones disponibles</h2>
    <ul class="list-group">
        {% for musica in songs %}
            <li class="list-group-item">
                <strong>{{ musica.cancion }}</strong> - {{ musica.artista }} <br>
                <em>Álbum: {{ musica.album }}</em> | Año: {{ musica.anio }} | Duración: {{ musica.duracion }} segundos <br>
                <p>{{ musica.descripcion }}</p>
                <p><strong>Email de contacto:</strong> {{ musica.email_contacto }}</p>

                <!-- Opción para editar, eliminar y reproducir -->
                <div class="btn-group mt-2">
                    <a href="{{ url_for('edit_song', id=musica.id) }}" class="btn btn-warning btn-sm">Editar</a>
                    <a href="{{ url_for('delete_song', id=musica.id) }}" class="btn btn-danger btn-sm ml-2" onclick="return confirm('¿Seguro que deseas desactivar esta canción?')">Desactivar</a>
                    <a href="{{ url_for('play_song', id=musica.id) }}" class="btn btn-info btn-sm ml-2">Reproducir</a>
                </div>

                <!-- Agregar a Playlist -->
                <div class="btn-group mt-2">
                    <button type="button" class="btn btn-dark" data-toggle="modal" data-target="#playlistModal{{ musica.id }}">
                        ➕ Agregar a Playlist
                    </button>
                </div>

                <!-- Modal para seleccionar la playlist -->
                <div class="modal fade" id="playlistModal{{ musica.id }}" tabindex="-1" role="dialog" aria-labelledby="playlistModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="playlistModalLabel">Seleccionar Playlist</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <ul class="list-group">
                                    {% for playlist in playlists %}
                                        <li class="list-group-item">
                                            <a href="{{ url_for('add_to_playlist', playlist_id=playlist.id, song_id=musica.id) }}">
                                                {{ playlist.nombre }}
                                            </a>
                                        </li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

            </li>
        {% endfor %}
    </ul>

    <!-- Formulario para crear una nueva playlist -->
    <h2 class="text-center mt-4">Crear una nueva Playlist</h2>
    <form action="/create_playlist" method="POST" class="mb-4">
        <input type="text" name="nombre" placeholder="Nombre de la Playlist" class="form-control" required>
        <button type="submit" class="btn btn-success mt-2">Crear Playlist</button>
    </form>

    <!-- Lista de Playlists -->
    <h2 class="text-center mt-5">Playlists</h2>
    <ul class="list-group">
        {% for playlist in playlists %}
            <li class="list-group-item">
                <strong>{{ playlist.nombre }}</strong>
                <a href="{{ url_for('playlist_detail', id=playlist.id) }}" class="btn btn-info btn-sm ml-2">Ver canciones</a>
            </li>
        {% else %}
            <p>No tienes playlists.</p>
        {% endfor %}
    </ul>
</div>

<!-- Dependencias de Bootstrap y jQuery -->
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
(index.html)

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detalles de la Playlist</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
</head>
<body>

<div class="container mt-5">
    <!-- Título de la Playlist -->
    <h1 class="text-center mb-4">{{ playlist.nombre }}</h1>

    <!-- Lista de Canciones en la Playlist -->
    <h3 class="text-center mb-4">Canciones en esta Playlist</h3>
    
    <div class="row">
        {% for musica in playlist.canciones %}
            <div class="col-md-4 mb-4">
                <div class="card shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">{{ musica.cancion }}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">{{ musica.artista }}</h6>
                        <p class="card-text">
                            <strong>Álbum:</strong> {{ musica.album }}<br>
                            <strong>Año:</strong> {{ musica.anio }}<br>
                            <strong>Duración:</strong> {{ musica.duracion }} segundos
                        </p>
                        <div class="btn-group" role="group" aria-label="Basic example">
                            <a href="{{ url_for('play_song', id=musica.id) }}" class="btn btn-info btn-sm">
                                <i class="fas fa-play"></i> Reproducir
                            </a>
                            <a href="{{ url_for('remove_from_playlist', playlist_id=playlist.id, song_id=musica.id) }}" class="btn btn-danger btn-sm" onclick="return confirm('¿Seguro que deseas eliminar esta canción de la playlist?')">
                                <i class="fas fa-trash"></i> Eliminar
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        {% else %}
            <p>No hay canciones en esta playlist.</p>
        {% endfor %}
    </div>

    <!-- Volver a la página principal -->
    <div class="text-center mt-4">
        <a href="{{ url_for('index') }}" class="btn btn-secondary">Volver a la Página Principal</a>
    </div>
</div>

<!-- Dependencias de Bootstrap y jQuery -->
<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

</body>
</html>
(playlist_detail.html

/* Estilos generales */
body {
    font-family: Arial, sans-serif;
    background-color: #f0f8ff;
    color: #333;
    margin: 0;
    padding: 0;
}

/* Estilos para el contenedor principal */
.container {
    max-width: 900px;
    margin: 50px auto;
    padding: 20px;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Títulos */
h1, h2 {
    text-align: center;
    color: #4caf50;
}

/* Estilos para los formularios */
form {
    margin-bottom: 30px;
}

label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
}

input[type="text"],
input[type="number"],
input[type="email"],
textarea {
    width: 100%;
    padding: 10px;
    margin-bottom: 15px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

button {
    padding: 10px 15px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #45a049;
}

/* Estilos para la lista de canciones */
ul {
    list-style-type: none;
    padding: 0;
}

ul li {
    background-color: #f9f9f9;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

ul li strong {
    color: #333;
    font-size: 18px;
}

ul li em {
    color: #777;
}

ul li p {
    margin: 5px 0;
}

/* Ajustes para pantallas pequeñas */
@media screen and (max-width: 768px) {
    .container {
        margin: 20px;
        padding: 15px;
    }
}

(style.css)

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reproductor de Música</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* Estilo para hacer el reproductor fijo */
        .player-fixed {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #212121;
            padding: 10px;
            color: white;
            box-shadow: 0px -2px 5px rgba(0, 0, 0, 0.3);
            z-index: 9999;
        }
        .player-fixed button {
            margin: 0 5px;
        }
        .progress {
            height: 5px;
        }
    </style>
</head>
<body>

<!-- Contenido principal (ya existe en tu código) -->
<div class="container mt-5 text-center" data-song-id="{{ current_song.id }}">
    <h1>Reproductor</h1>
    <h3>{{ current_song.cancion }} - {{ current_song.artista }}</h3>
    <p>Álbum: {{ current_song.album }} | Año: {{ current_song.anio }}</p>
    <div id="estado" class="alert alert-success mt-3" style="display:none;">
        Reproduciendo canción...
    </div>
    <button id="playPause" class="btn btn-success">Reproducir</button>
    <button id="next" class="btn btn-primary ml-2">Siguiente</button>

    <!-- Barra de progreso -->
    <div class="progress mt-3">
        <div id="progressBar" class="progress-bar progress-bar-striped" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
    </div>
</div>

<!-- Reproductor fijo en la parte inferior -->
<div class="player-fixed">
    <div class="container">
        <h5>Reproduciendo: {{ current_song.cancion }} - {{ current_song.artista }}</h5>
        <button id="playPauseFixed" class="btn btn-success">Reproducir</button>
        <button id="nextFixed" class="btn btn-primary ml-2">Siguiente</button>
        <!-- Barra de progreso -->
        <div class="progress mt-3">
            <div id="progressBarFixed" class="progress-bar progress-bar-striped" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
    </div>
</div>

<script>
    const container = document.querySelector('.container');
    const songId = parseInt(container.dataset.songId);

    const playPauseBtn = document.getElementById('playPause');
    const nextBtn = document.getElementById('next');
    const playPauseBtnFixed = document.getElementById('playPauseFixed');
    const nextBtnFixed = document.getElementById('nextFixed');
    const estado = document.getElementById('estado');
    const progressBar = document.getElementById('progressBar');
    const progressBarFixed = document.getElementById('progressBarFixed');

    let reproduciendo = false;
    let progreso = 0;

    // Reproducción con el botón principal
    playPauseBtn.addEventListener('click', () => {
        reproduciendo = !reproduciendo;

        if (reproduciendo) {
            estado.style.display = 'block';
            playPauseBtn.textContent = 'Pausar';
            playPauseBtnFixed.textContent = 'Pausar';
            // Iniciar barra de progreso
            progressInterval = setInterval(updateProgressBar, 1000);  // Actualiza cada segundo
        } else {
            estado.style.display = 'none';
            playPauseBtn.textContent = 'Reproducir';
            playPauseBtnFixed.textContent = 'Reproducir';
            clearInterval(progressInterval);  // Detener la actualización de la barra
        }
    });

    // Reproducción con el botón del reproductor fijo
    playPauseBtnFixed.addEventListener('click', () => {
        playPauseBtn.click();
    });

    // Cambio de canción
    nextBtn.addEventListener('click', () => {
        const nextSongId = songId + 1;
        window.location.href = "/play/" + nextSongId;
    });

    nextBtnFixed.addEventListener('click', () => {
        nextBtn.click();
    });

    function updateProgressBar() {
        if (progreso < 100) {
            progreso += 1;
            progressBar.style.width = `${progreso}%`;
            progressBar.setAttribute('aria-valuenow', progreso);
            progressBarFixed.style.width = `${progreso}%`;
            progressBarFixed.setAttribute('aria-valuenow', progreso);
        }
    }
</script>

</body>
</html>

(player.html)

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Canción</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

    <div class="container mt-5">
        <h1 class="text-center text-primary">Editar Canción</h1>
        <form action="/edit_song/{{ musica.id }}" method="POST" class="border p-4 rounded shadow">
            <div class="form-group">
                <label for="cancion">Canción:</label>
                <input type="text" id="cancion" name="cancion" value="{{ musica.cancion }}" class="form-control" required><br><br>
            </div>

            <div class="form-group">
                <label for="artista">Artista:</label>
                <input type="text" id="artista" name="artista" value="{{ musica.artista }}" class="form-control" required><br><br>
            </div>

            <div class="form-group">
                <label for="album">Álbum:</label>
                <input type="text" id="album" name="album" value="{{ musica.album }}" class="form-control" required><br><br>
            </div>

            <div class="form-group">
                <label for="anio">Año:</label>
                <input type="number" id="anio" name="anio" value="{{ musica.anio }}" class="form-control" required><br><br>
            </div>

            <div class="form-group">
                <label for="duracion">Duración (en segundos):</label>
                <input type="number" id="duracion" name="duracion" value="{{ musica.duracion }}" class="form-control" required><br><br>
            </div>

            <div class="form-group">
                <label for="descripcion">Descripción:</label>
                <textarea id="descripcion" name="descripcion" class="form-control" required>{{ musica.descripcion }}</textarea><br><br>
            </div>

            <div class="form-group">
                <label for="email_contacto">Email de contacto:</label>
                <input type="email" id="email_contacto" name="email_contacto" value="{{ musica.email_contacto }}" class="form-control" required><br><br>
            </div>

            <button type="submit" class="btn btn-primary btn-block">Guardar Cambios</button>
        </form>
    </div>

</body>
</html>
(edit_song.html)
