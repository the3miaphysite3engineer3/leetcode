#!/usr/bin/env node
/**
 * Runner for JavaScript LeetCode solutions.
 *
 * Usage: node js_runner.js <solution_file> <function_name> <inputs_json>
 *
 * Loads the solution file inside a sandboxed VM context, calls the specified
 * function with the given inputs, and prints the result as JSON.
 *
 * Since JS solution files often define multiple approaches using the same
 * variable name, the last definition wins (which is typically the most
 * optimized solution).
 */

const fs = require('fs');
const vm = require('vm');

function main() {
    if (process.argv.length !== 5) {
        console.error(
            'Usage: node js_runner.js <solution_file> <function_name> <inputs_json>',
        );
        process.exit(1);
    }

    const solutionFile = process.argv[2];
    const functionName = process.argv[3];
    const inputs = JSON.parse(process.argv[4]);

    // Read solution code
    const code = fs.readFileSync(solutionFile, 'utf8');

    // Execute solution code in a sandboxed context
    // The sandbox provides standard globals needed by LeetCode solutions
    const sandbox = {
        Map,
        Set,
        Array,
        Object,
        Math,
        Number,
        String,
        Boolean,
        parseInt,
        parseFloat,
        isNaN,
        isFinite,
        Infinity,
        NaN,
        undefined,
        console,
    };
    vm.createContext(sandbox);
    vm.runInContext(code, sandbox);

    // Get the function reference from the sandbox
    const fn = sandbox[functionName];
    if (typeof fn !== 'function') {
        console.error(`Error: '${functionName}' is not a function`);
        process.exit(1);
    }

    // Call the function with inputs
    const result = fn(...inputs);

    // Output result as JSON
    console.log(JSON.stringify(result));
}

main();
