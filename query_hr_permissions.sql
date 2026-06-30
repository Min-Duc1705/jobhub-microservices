SELECT p."Name", p."Method", p."ApiPath" FROM "Permissions" p JOIN "RolePermissions" rp ON p."Id" = rp."PermissionsId" JOIN "Roles" r ON rp."RolesId" = r."Id" WHERE r."Name" = 'HR';
