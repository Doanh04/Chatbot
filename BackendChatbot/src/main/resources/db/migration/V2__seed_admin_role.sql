INSERT INTO roles (id, name)
VALUES ('989cff1e-c885-45c7-bd91-0da09e16bada', 'ADMIN')
ON CONFLICT (name) DO NOTHING;
