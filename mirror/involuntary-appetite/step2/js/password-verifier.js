(() => {
  const normalize = (value) => value.trim().toLowerCase().replace(/\s+/g, "");

  const loadModule = async () => {
    const response = await fetch("/step2/password-checker.wasm", { cache: "no-store" });
    if (!response.ok) throw new Error(`WASM load failed: ${response.status}`);
    const bytes = await response.arrayBuffer();
    const { instance } = await WebAssembly.instantiate(bytes);
    return instance.exports;
  };

  const ready = loadModule();

  window.passwordVerifier = {
    ready,
    async verify(scope, value) {
      const exports = await ready;
      const normalized = normalize(value);
      exports.beginPassword(scope);
      for (let index = 0; index < normalized.length; index += 1) {
        exports.writePasswordByte(index, normalized.charCodeAt(index));
      }
      return exports.finishPassword(normalized.length) === 1;
    }
  };
})();
