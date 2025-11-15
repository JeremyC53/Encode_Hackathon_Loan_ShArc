import * as browserifyZlib from "browserify-zlib";

type BrowserifyZlib = typeof browserifyZlib & {
  constants?: Record<string, number>;
  createBrotliDecompress?: typeof browserifyZlib.createGunzip;
};

const constants = {
  ...browserifyZlib,
  Z_SYNC_FLUSH: (browserifyZlib as BrowserifyZlib).Z_SYNC_FLUSH ?? 2,
  BROTLI_OPERATION_FLUSH: 2,
};

const zlibShim: BrowserifyZlib = {
  ...(browserifyZlib as BrowserifyZlib),
  constants,
  createBrotliDecompress: undefined,
};

export default zlibShim;
export { constants };

