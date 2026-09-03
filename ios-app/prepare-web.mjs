import { cpSync, existsSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const source = resolve("..", "floodsafe-nepal");
const target = resolve("www");
if (!existsSync(source)) throw new Error("Expected ../floodsafe-nepal beside ios-app.");
if (existsSync(target)) rmSync(target, { recursive: true, force: true });
cpSync(source, target, { recursive: true });
console.log("Copied FloodSafe Nepal web files into ios-app/www.");
