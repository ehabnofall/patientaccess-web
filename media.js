// Picks photos and shrinks them in the browser (longest side maxSide, WebP or
// JPEG) before upload. Resolves to a list of data URLs.
window.paPickImages = function (multiple, maxSide) {
  return new Promise(function (resolve) {
    var input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/jpeg,image/png,image/webp,image/*';
    input.multiple = !!multiple;
    input.style.display = 'none';
    document.body.appendChild(input);
    var done = false;
    function finish(v) { if (done) return; done = true; input.remove(); resolve(v); }
    function toBlob(c, type, q) { return new Promise(function (r) { c.toBlob(r, type, q); }); }
    function dataUrl(b) { return new Promise(function (r) { var f = new FileReader(); f.onload = function () { r(f.result); }; f.onerror = function () { r(null); }; f.readAsDataURL(b); }); }
    input.addEventListener('change', async function () {
      var out = [];
      var files = Array.prototype.slice.call(input.files || [], 0, 15);
      for (var i = 0; i < files.length; i++) {
        try {
          var bmp = await createImageBitmap(files[i]);
          var s = Math.min(1, maxSide / Math.max(bmp.width, bmp.height));
          var c = document.createElement('canvas');
          c.width = Math.round(bmp.width * s); c.height = Math.round(bmp.height * s);
          c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
          var b = await toBlob(c, 'image/webp', 0.82);
          if (!b || b.type !== 'image/webp') b = await toBlob(c, 'image/jpeg', 0.85);
          var u = b && await dataUrl(b);
          if (u) out.push(u);
        } catch (e) { /* skip unreadable files */ }
      }
      finish(out);
    });
    input.addEventListener('cancel', function () { finish([]); });
    input.click();
  });
};
