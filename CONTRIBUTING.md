# Cómo proponer un curso

La forma más fácil es abrir un issue con el formulario **Proponer curso**. Si te animás al pull request, seguí estos pasos.

## Qué entra

1. Gratis de verdad: se puede hacer completo sin pagar. Si el certificado se paga, el curso entra igual con "No" en la última columna.
2. Oficial: el enlace va directo al sitio de quien da el curso (Google, Microsoft Learn, freeCodeCamp, Coursera, la documentación oficial, etc.).
3. De calidad: lo hiciste o lo revisaste y te sirvió. Preferimos cinco buenos a veinte de relleno.

## Qué no entra

1. Enlaces de afiliado, acortadores (bit.ly y similares) o enlaces con códigos de referido.
2. Copias de cursos de pago subidas por otra persona.
3. Cursos que solo son gratis durante una prueba que después cobra.
4. Cursos que no se pudieron abrir para comprobarlos.

## Cómo agregarlo

1. Hacé un fork del repo y creá una rama: `git switch -c curso_nombre_corto`.
2. Agregá una fila en la tabla de la ruta que corresponde en `README.md`:

   ```
   | [Nombre del curso](https://enlace-oficial) | Plataforma | EN | Principiante | ~10 | No |
   ```

   - Idioma: `EN`, `ES` o `EN, ES`.
   - Nivel: `Principiante`, `Intermedio`, `Avanzado` o `Todos los niveles`.
   - Horas: un número (`8`), aproximado (`~10`), un rango (`15 a 20`), `<1` o `Variable`.
   - Certificado gratis: `Sí`, `No` o `Insignia`.

3. Revisá formato y enlaces en tu compu (solo necesitás Python):

   ```
   python herramientas/revisar_enlaces.py
   ```

   Tiene que decir "Todo bien". Sin internet, `--sin-red` revisa solo el formato.

4. Abrí el pull request y contá en la descripción por qué vale la pena el curso.

En cada pull request, GitHub Actions corre la revisión de formato. Los enlaces se revisan con internet desde la pestaña Actions, porque algunos sitios bloquean a los servidores de GitHub.

## Si un curso se cae

Abrí un issue con el formulario **Enlace caído o dato equivocado**, o mandá el pull request quitando la fila.
