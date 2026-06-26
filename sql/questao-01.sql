-- Questão 1: Retorna nome, e-mail, papel e claims de cada usuário
SELECT
    u.name,
    u.email,
    r.description   AS role,
    c.description   AS claim
FROM users u
JOIN roles r        ON r.id = u.role_id
JOIN user_claims uc ON uc.user_id = u.id
JOIN claims c       ON c.id = uc.claim_id
WHERE c.active = true;
