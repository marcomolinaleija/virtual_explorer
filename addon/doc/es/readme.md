# Virtual Explorer

## ¿Qué es?

**Virtual Explorer** es un complemento para el lector de pantalla NVDA que te permite gestionar y navegar por tus rutas de archivos y carpetas favoritas de una manera rápida y eficiente. Funciona como un **explorador de archivos virtual** directamente en NVDA, permitiéndote explorar el contenido de las carpetas que has guardado.

## Características Principales

*   **Gestión de Favoritos:** Añade, renombra, elimina y fija tus rutas favoritas.
*   **Organización por Categorías:** Agrupa tus rutas en categorías personalizadas para tener un acceso más ordenado.
*   **Navegación Virtual:** Explora el contenido de las carpetas guardadas sin necesidad de abrir el explorador de archivos de Windows.
*   **Menú de Acciones:** Realiza operaciones básicas como Copiar, Cortar y Pegar directamente desde el explorador virtual.
*   **Marcadores Dinámicos:** Utiliza marcadores como `$desktop` o `$downloads` para acceder rápidamente a carpetas comunes del sistema.

## Atajos de Teclado

Los atajos de teclado se pueden personalizar desde el diálogo de **Gestos de Entrada** de NVDA, bajo la categoría "Virtual Explorer".

### Navegación General
*   `NVDA+Alt+A`: Abre el diálogo de administración para añadir, renombrar y gestionar rutas y categorías.
*   `NVDA+Alt+J`: Navega al elemento anterior.
*   `NVDA+Alt+K`: Navega al elemento siguiente.
*   `NVDA+Alt+L`: Entra en una carpeta para explorar su contenido o abre un archivo. También sirve para activar una opción en el menú de acciones.
*   `NVDA+Alt+Enter`: Abre el archivo o carpeta con la aplicación predeterminada. También sirve para activar una opción en el menú de acciones.
*   `NVDA+Alt+Retroceso`: Vuelve a la carpeta anterior o sale del explorador virtual.
*   `Alt+NVDA+Delete`: Elimina la ruta favorita seleccionada. **Nota:** Esta acción solo funciona en la lista principal de favoritos, no dentro de una carpeta que estés explorando.
*   `Suprimir`: Dentro del diálogo de administración (`NVDA+Alt+A`), elimina la ruta seleccionada en la lista.

### Navegación por Categorías
*   `NVDA+Alt+FlechaArriba`: Navega a la categoría anterior.
*   `NVDA+Alt+FlechaAbajo`: Navega a la categoría siguiente.

### Menú de Acciones
*   `NVDA+Alt+Espacio`: Muestra un menú contextual con acciones para el elemento seleccionado. Las acciones disponibles son:
    *   **Copiar:** Copia el archivo/carpeta.
    *   **Cortar:** Corta el archivo/carpeta.
    *   **Pegar:** Pega el contenido del portapapeles en la carpeta actual (esta opción solo aparece si hay algo en el portapapeles).
    *   **Copiar como ruta de acceso:** Copia la ruta completa del archivo/carpeta al portapapeles.

**Nota:** Para **renombrar** una ruta o categoría, debes usar las opciones correspondientes dentro del diálogo de administración (`NVDA+Alt+A`).

## ¿Qué son los marcadores?

Los marcadores son palabras clave que comienzan con `$` y que apuntan a rutas predeterminadas del sistema. Esto te permite acceder a ellas rápidamente sin escribir la ruta completa.

*   `$users`: Ruta de tu perfil de usuario (ej. `C:\Users\TuUsuario`).
*   `$desktop`: Ruta de tu escritorio.
*   `$downloads`: Ruta de la carpeta de descargas.
*   `$documents`: Ruta de la carpeta de documentos.
*   `$videos`: Ruta de la carpeta de videos.
*   `$pictures`: Ruta de la carpeta de imágenes.

**Ejemplo de uso:** `$desktop\MiCarpeta` se resolverá a `C:\Users\TuUsuario\Desktop\MiCarpeta`.

## Notas

Este complemento es una bifurcación (fork) y una reimaginación del antiguo complemento [Rutas Favoritas](https://github.com/reyes2005/rutas_fav), manteniendo su idea original pero con un código y características renovadas.

Si deseas contribuir con una pull request o apertura de una issue en dado caso se presenten problemas, puedes hacerlo. Así mismo, si deseas hacerme algún comentario o sugerencia, puedes escribir al [correo](mailto:marcoleija@marco-ml.com)  
De la misma manera, si deseas realizar un donativo para que el desarrollo de este y próximos complementos continúen, no dudes en dar click [aquí](https://paypal.me/paymentToMl).  

## Changelog

### v2.0.0
*   **Renombrado a Virtual Explorer:** El complemento ha sido renombrado de "Rutas fav" a "Virtual Explorer" para reflejar mejor su funcionalidad.
*   **Gestión de Categorías:** Se ha añadido la capacidad de organizar las rutas favoritas por categorías, incluyendo la opción de renombrarlas desde el diálogo de administración.
*   **Menú de Acciones Contextual:** Se implementó un menú contextual (`NVDA+Alt+Espacio`) que permite realizar operaciones de archivo (Copiar, Cortar, Pegar) y copiar rutas.
*   **Gestión Mejorada:** La funcionalidad para renombrar y fijar/desfijar rutas ahora se encuentra en el diálogo de administración para una gestión más centralizada.
*   **Nuevos Atajos:** Se han añadido atajos para la navegación por categorías.
*   **Mejoras de Usabilidad:** El lector de pantalla ahora anuncia el número de elementos en cada categoría.

### v1.1.0
*   Se ha implementado un explorador de archivos virtual. Ahora es posible entrar en las carpetas guardadas para navegar por su contenido.
*   Se han añadido nuevos atajos de teclado para entrar, salir y abrir carpetas/archivos.
*   Se ha refactorizado la lógica interna para soportar la navegación jerárquica.

### v1.0.2
*   Corrección de la anidación de encabezados en el readme.
*   Corrección de errores menores de código.

### v1.0.1
*   Corrección de errores menores.

### v1.0
*   Versión inicial del complemento.
