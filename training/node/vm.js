/*
usage: 
node vm.js programCode assertions

arguments:
programCode is a STRING containing a js program
assertions is an ARRAY of strings representing assertions made using node assertions


output: 
an array printed to the console (and collected by Django via subprocess.check_output()) where each entry 
corresponds to an assertion and is an object:
{ 
    id: Number,
    assertion: String,
    public: Boolean,
    passed: Boolean,
    error: String,
} 
where id is the id of the assertion (as in the Django database),
assertion is the string containing the assertion verbatim,
public indicates whether the assertion is to be shown to the user or it's secret,
passed represents the outcome of running the assertion on the program,
and error is only present if the assertion failed
*/

// The VM2 module allows to execute arbitrary code safely using a sandboxed, secure virtual machine
const { VM } = require('vm2')
const assert = require('assert')
const AssertionError = require('assert').AssertionError
const timeout = 1000

// instantiation of the vm that'll run the user-submitted program
const safevm = new VM({
  timeout, // set timeout to prevent endless loops from running forever
  sandbox: {
    prettyPrintError,
    prettyPrintAssertionError,
    assert,
    AssertionError
  }
})

function prettyPrintError (e) {
  const tokens = e.stack.split(/(.*)at (new Script(.*))?vm.js:([0-9]+)(.*)/)
  const rawStr = tokens[0] // error message

  if (rawStr.match(/execution timed out/)) {
    // time out: no other information available
    return `Execution timed out after ${timeout} ms`
  }

  const formattedStr = rawStr.replace(
    /(.*)vm.js:([0-9]+):?([0-9]+)?(.*)/g,
    function (a, b, c, d) {
      return `on line ${parseInt(c) - 1}` + (d ? `, at position ${d})` : '')
    }
  ) // actual line of the error is one less than what's detected due to an additional line of code injected in the vm
  return formattedStr
}

// does the same as prettyPrintError(), but it's specifically designed to work with AssertionErrors
function prettyPrintAssertionError (e) {
  const expected = e.expected
  const actual = e.actual
  const [errMsg, _] = e.stack.split('\n')
  return (
    errMsg +
    ' expected value ' +
    JSON.stringify(expected) +
    ', but got ' +
    JSON.stringify(actual)
  )
}

const escapeBackTicks = t => t.replace(/`/g, '\\`')

const userCode = process.argv[2]

const assertions = JSON.parse(process.argv[3])

// turn array of strings representing assertions to a series of try-catch blocks
//  where those assertions are evaluated and the result is pushed to an array
// the resulting string will be inlined into the program that the vm will run
const assertionString = assertions
  .map(
    (
      a // put assertion into a try-catch block
    ) =>
      `
        ran = {id: ${a.id}, assertion: \`${escapeBackTicks(
        a.assertion
      )}\`, is_public: ${a.is_public}}
        try {
            ${a.assertion} // run the assertion
            ran.passed = true // if no exception is thrown, the test case passed
        } catch(e) {
            ran.passed = false
            if(e instanceof AssertionError) {
                ran.error = prettyPrintAssertionError(e)
            } else {
                ran.error = prettyPrintError(e)
            }
        }
        output_wquewoajfjoiwqi.push(ran)
    `
  )
  .reduce((a, b) => a + b, '') // reduce array of strings to a string
// support for executing the user-submitted program
// contains a utility function to stringify errors, the user code, and a series of try-catch's
// where assertions are ran against the user code; the program evaluates to an array of outcomes
// resulting from those assertions
const runnableProgram = `const output_wquewoajfjoiwqi = []; const arr_jiodferwqjefio = Array; const push_djiowqufewio = Array.prototype.push; const shift_dfehwioioefn = Array.prototype.shift
${userCode}
// USER CODE ENDS HERE

// restore array prototype and relevant array methods in case user tampered with them
Array = arr_jiodferwqjefio
Array.prototype.push = push_djiowqufewio;
Array.prototype.shift = shift_dfehwioioefn;

if(Object.isFrozen(output_wquewoajfjoiwqi)) {
    // abort if user intentionally froze the output array
    throw new Error("Malicious user code froze vm's output array")
}

while(output_wquewoajfjoiwqi.length) {
    output_wquewoajfjoiwqi.shift() // make sure the output array is empty
}

// inline assertions

${assertionString}

// output outcome object to console
output_wquewoajfjoiwqi`

try {
  const outcome = safevm.run(runnableProgram) // run program
  console.log(JSON.stringify({ tests: outcome })) // output outcome so Django can collect it
} catch (e) {
  console.log(JSON.stringify({ error: prettyPrintError(e) }))
}
