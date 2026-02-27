/**
 * Drag & drop upload para el widget ImageDropWidget en el admin de Django.
 * Maneja: drag-and-drop, click para seleccionar, preview inmediato, upload via fetch.
 */
(function () {
  "use strict";

  var MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
  var ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];

  function initWidget(widget) {
    var input = widget.querySelector("input[type=text]");
    var dropZone = widget.querySelector(".image-drop-zone");
    var statusEl = widget.querySelector(".image-drop-status");
    var uploadUrl = widget.dataset.uploadUrl;

    if (!input || !dropZone || !uploadUrl) return;

    // ── Click para seleccionar archivo ───────────────────────────────────────
    dropZone.addEventListener("click", function () {
      var fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = "image/*";
      fileInput.addEventListener("change", function (e) {
        var file = e.target.files && e.target.files[0];
        if (file) handleFile(file);
      });
      fileInput.click();
    });

    // ── Drag events ──────────────────────────────────────────────────────────
    dropZone.addEventListener("dragover", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("is-dragging");
    });

    dropZone.addEventListener("dragleave", function (e) {
      // Solo quitar la clase si el cursor salió del dropZone (no de un hijo)
      if (!dropZone.contains(e.relatedTarget)) {
        dropZone.classList.remove("is-dragging");
      }
    });

    dropZone.addEventListener("drop", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("is-dragging");

      var files = e.dataTransfer && e.dataTransfer.files;
      var file = files && files[0];

      if (!file) return;

      if (!file.type.startsWith("image/")) {
        showStatus("error", "✗ Solo se permiten archivos de imagen.");
        return;
      }

      handleFile(file);
    });

    // ── Lógica de manejo de archivo ──────────────────────────────────────────
    function handleFile(file) {
      // Validar tipo
      if (ALLOWED_TYPES.indexOf(file.type) === -1) {
        showStatus("error", "✗ Formato no soportado. Usá JPG, PNG, GIF o WebP.");
        return;
      }

      // Validar tamaño
      if (file.size > MAX_SIZE_BYTES) {
        showStatus("error", "✗ La imagen supera el límite de 5MB.");
        return;
      }

      // Preview local inmediato mientras se sube
      var reader = new FileReader();
      reader.onload = function (e) {
        renderPreview(e.target.result);
      };
      reader.readAsDataURL(file);

      uploadFile(file);
    }

    function uploadFile(file) {
      showStatus("loading", "Subiendo imagen…");
      dropZone.classList.add("is-loading");

      var csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
      if (!csrfInput) {
        showStatus("error", "✗ CSRF token no encontrado. Recargá la página.");
        dropZone.classList.remove("is-loading");
        return;
      }

      var formData = new FormData();
      formData.append("image", file);

      fetch(uploadUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfInput.value },
        body: formData,
      })
        .then(function (res) {
          if (!res.ok) {
            return res.json().then(function (data) {
              throw new Error(data.error || "Error " + res.status);
            });
          }
          return res.json();
        })
        .then(function (data) {
          if (!data.url) throw new Error("La respuesta no incluye una URL.");
          input.value = data.url;
          renderPreview(data.url);
          showStatus("success", "✓ Imagen subida correctamente.");
          // Limpiar mensaje de éxito después de 3s
          setTimeout(function () {
            clearStatus();
          }, 3000);
        })
        .catch(function (err) {
          showStatus("error", "✗ " + (err.message || "Error al subir la imagen."));
          // Si falló el upload, limpiar el preview optimista
          renderPreview(input.value || null);
        })
        .finally(function () {
          dropZone.classList.remove("is-loading");
        });
    }

    // ── Preview ──────────────────────────────────────────────────────────────
    function renderPreview(url) {
      var preview = widget.querySelector(".image-drop-preview");

      if (!url) {
        if (preview) preview.style.display = "none";
        return;
      }

      if (!preview) {
        preview = document.createElement("div");
        preview.className = "image-drop-preview";
        widget.appendChild(preview);
      }

      var img = preview.querySelector("img");
      if (!img) {
        img = document.createElement("img");
        img.alt = "Preview de imagen";
        preview.appendChild(img);
      }

      img.src = url;
      preview.style.display = "block";
    }

    // ── Status messages ──────────────────────────────────────────────────────
    function showStatus(type, message) {
      statusEl.className = "image-drop-status is-" + type;
      statusEl.textContent = message;
    }

    function clearStatus() {
      statusEl.className = "image-drop-status";
      statusEl.textContent = "";
    }
  }

  // ── Init ─────────────────────────────────────────────────────────────────
  function init() {
    document.querySelectorAll(".image-drop-widget").forEach(initWidget);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
