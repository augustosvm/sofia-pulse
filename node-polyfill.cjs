/**
 * Node.js 18 + undici polyfill
 * Este arquivo DEVE ser carregado ANTES de qualquer outro código
 */

// Fix File global for undici
if (typeof File === 'undefined') {
  globalThis.File = class File extends Blob {
    constructor(bits, name, options) {
      super(bits, options);
      this.name = name;
      this.lastModified = options?.lastModified || Date.now();
    }
  };
}

console.log('✅ File polyfill loaded');
