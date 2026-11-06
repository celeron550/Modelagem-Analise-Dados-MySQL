CREATE TABLE Usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Avaliacao_Musica (
    id_avaliacao INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_musica INT NOT NULL,
    nota DECIMAL(3,1) NOT NULL CHECK (nota >= 0 AND nota <= 10), -- Escala de 0 a 10
    comentario TEXT,
    data_avaliacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_musica) REFERENCES Musica(id_musica) ON DELETE CASCADE,
    UNIQUE(id_usuario, id_musica) -- Garante que um usuário avalie a mesma música apenas uma vez
);