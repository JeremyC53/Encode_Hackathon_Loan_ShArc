import { Buffer } from "buffer";
import process from "process";

type GlobalScope = typeof globalThis & {
  Buffer?: typeof Buffer;
  process?: NodeJS.Process;
  global?: typeof globalThis;
};

const globalScope = globalThis as GlobalScope;
const windowScope = window as Window &
  Partial<{
    Buffer: typeof Buffer;
    process: NodeJS.Process;
    global: typeof globalThis;
  }>;

if (typeof globalScope.Buffer === "undefined") {
  globalScope.Buffer = Buffer;
}

if (typeof globalScope.process === "undefined") {
  globalScope.process = process;
}

const globalProcess = globalScope.process as typeof process & {
  browser?: boolean;
  version?: string;
};

if (!globalProcess.browser) {
  (globalProcess as any).browser = true;
}
if (!globalProcess.version) {
  (globalProcess as any).version = "0";
}
if (!globalProcess.nextTick) {
  globalProcess.nextTick = (...args: Parameters<typeof process.nextTick>) =>
    process.nextTick(...args);
}

if (typeof globalScope.global === "undefined") {
  globalScope.global = globalScope;
}

if (typeof windowScope.Buffer === "undefined") {
  windowScope.Buffer = Buffer;
}

if (typeof windowScope.process === "undefined") {
  windowScope.process = process;
}

const windowProcess = windowScope.process as typeof process & {
  browser?: boolean;
  version?: string;
};

if (!windowProcess.browser) {
  (windowProcess as any).browser = true;
}
if (!windowProcess.version) {
  (windowProcess as any).version = "0";
}
if (!windowProcess.nextTick) {
  windowProcess.nextTick = (...args: Parameters<typeof process.nextTick>) =>
    process.nextTick(...args);
}

if (typeof windowScope.global === "undefined") {
  windowScope.global = globalScope;
}

