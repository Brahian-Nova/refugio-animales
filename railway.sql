INSERT INTO usuarios(name,email,password)
VALUES('Admin','admin@gmail.com','1234');

INSERT INTO usuarios(name,email,password)
VALUES('Brahian Novoa','Brahian.novoa@gmail.com','1234');

INSERT INTO usuarios(name,email,password)
VALUES('Kevin Aldana','kevin.aldana@gmail.com','1234');

SELECT * FROM usuarios;

CREATE TABLE animales (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    especie TEXT NOT NULL,
    edad INT,
    adoptado BOOLEAN DEFAULT FALSE,
    usuario_id INT REFERENCES usuarios(id)
);

INSERT INTO animales (nombre,especie,edad,usuario_id)
VALUES
('max','Perro',3,1),
('michi','Gato',2,2);

SELECT * FROM animales;

ALTER TABLE usuarios
RENAME COLUMN name TO nombre;
