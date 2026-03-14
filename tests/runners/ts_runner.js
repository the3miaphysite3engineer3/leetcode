#!/usr/bin/env node
/**
 * Runner for TypeScript LeetCode solutions.
 *
 * Usage: node ts_runner.js <solution_file> <function_name> <inputs_json>
 *
 * Strips TypeScript type annotations and runs the code as JavaScript.
 * Handles common patterns found in LeetCode TypeScript solutions.
 */

const fs = require('fs');
const path = require('path');

/**
 * Strip TypeScript type annotations to produce valid JavaScript.
 * Handles common patterns in LeetCode solutions.
 */
function stripTypes(code) {
    // Remove single-line type imports
    code = code.replace(
        /^import\s+type\s+.*?;?\s*$/gm,
        '',
    );

    // Remove function return type annotations: ): Type {
    code = code.replace(
        /\)\s*:\s*([^{=]*?)\s*\{/g,
        ') {',
    );

    // Remove parameter type annotations in function declarations
    // Match: (param: Type, param2: Type) but be careful with objects and generics
    code = code.replace(
        /(\w+)\s*:\s*(number|string|boolean|null|undefined|any|void|never|unknown|object|symbol|bigint)([\[\]]*)/g,
        '$1',
    );

    // Handle complex parameter types like { [key: number]: number }
    code = code.replace(
        /(\w+)\s*:\s*\{[^}]*\}/g,
        '$1',
    );

    // Handle array type annotations like: number[], string[]
    code = code.replace(
        /(\w+)\s*:\s*\w+\[\]/g,
        '$1',
    );

    // Handle generic types like Map<number, number>
    code = code.replace(
        /(\w+)\s*:\s*(?:Map|Set|Array|Record|Partial|Required|Pick|Omit)<[^>]+>/g,
        '$1',
    );

    // Remove variable type annotations: let/const x: Type = ...
    code = code.replace(
        /(let|const|var)\s+(\w+)\s*:\s*[^=;]+\s*=/g,
        '$1 $2 =',
    );

    // Remove 'as Type' type assertions
    code = code.replace(
        /\s+as\s+\w+(\[\])?/g,
        '',
    );

    // Remove angle bracket type assertions: <Type>value
    code = code.replace(
        /<(number|string|boolean|any)>/g,
        '',
    );

    return code;
}

function main() {
    if (process.argv.length !== 5) {
        console.error(
            'Usage: node ts_runner.js <solution_file> <function_name> <inputs_json>',
        );
        process.exit(1);
    }

    const solutionFile = process.argv[2];
    const functionName = process.argv[3];
    const inputs = JSON.parse(process.argv[4]);

    // Read and strip types from TypeScript code
    const tsCode = fs.readFileSync(solutionFile, 'utf8');
    const jsCode = stripTypes(tsCode);

    // Execute the converted code
    eval(jsCode);

    // Get the function reference
    const fn = eval(functionName);
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
