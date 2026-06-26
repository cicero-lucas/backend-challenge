-- Seed: dados iniciais para desenvolvimento e demonstração

INSERT INTO roles (description) VALUES
    ('admin'),
    ('editor'),
    ('viewer');

INSERT INTO claims (description, active) VALUES
    ('users:read',   true),
    ('users:write',  true),
    ('roles:read',   true),
    ('roles:write',  true),
    ('reports:read', true);
