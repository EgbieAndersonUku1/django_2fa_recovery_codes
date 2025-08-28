import { warnError } from "./logger.js";
import { toTitle } from "./utils.js";


/**
 * Creates a complete HTML table element with an optional id and CSS classes.
 * 
 * Example:
 *   const table = buildTable(
 *     ["Name", "Age", "Email"],          // column headers
 *     [
 *       ["Alice", 30, "alice@email.com"], // body rows each element inside the array (row) is a cell for that row
 *       ["Bob", 25, "bob@email.com"]
 *     ],
 *     { id: "usersTable", classList: ["striped", "hover"] } // optional table attributes
 *   );
 * 
 * Produces:
 *   <table id="usersTable" class="striped hover">
 *       <thead>
 *           <tr>
 *               <th scope="col">Name</th>
 *               <th scope="col">Age</th>
 *               <th scope="col">Email</th>
 *           </tr>
 *       </thead>
 *       <tbody>
 *           <tr>
 *               <td>Alice</td>
 *               <td>30</td>
 *               <td>alice@email.com</td>
 *           </tr>
 *           <tr>
 *               <td>Bob</td>
 *               <td>25</td>
 *               <td>bob@email.com</td>
 *           </tr>
 *       </tbody>
 *   </table>
 * 
 * @param {Array<string>} columnHeadersList - List of column header labels.
 * @param {Array<Array>} bodyDataList - Array of rows, where each row is an array of cell values.
 * @param {Object} [selectors] - Optional object with id and classList to apply to the table.
 * @param {string} [selectors.id] - The id to assign to the table.
 * @param {Array<string>} [selectors.classList] - An array of CSS class names to add.
 * @returns {HTMLTableElement} The fully constructed table element.
 */
export function HTMLTableBuilder(columnHeadersList, rowDataList, options = {}) {

    const tableElement     = document.createElement("table");
    const THElement        = buildTableHead(columnHeadersList);
    const tBody            = buildTableBody(rowDataList)

    tableElement.appendChild(THElement)
    tableElement.appendChild(tBody);

    const table = applyTableAttributes(tableElement, options)
    return table;
}



/**
 * Applies an id and a list of CSS classes to a table element.
 * 
 * Example:
 *   const table = document.createElement("table");
 *   addSelectorsToTable(table, {
 *     id: "usersTable",
 *     classList: ["striped", "hover", "bordered"]
 *   });
 * 
 * Produces:
 *   <table id="usersTable" class="striped hover bordered"></table>
 * 
 * @param {HTMLTableElement} table - The table element to modify.
 * @param {Object} selectors - An object containing the id and CSS classes to apply.
 * @param {string} [selectors.id] - The id to assign to the table.
 * @param {Array<string>} [selectors.classList] - An array of CSS class names to add.
 * @returns {HTMLTableElement} The updated table element.
 */
function applyTableAttributes(table, selectors) {
    if (!(table instanceof HTMLTableElement)) {
        throw new Error(
            `Invalid argument: expected an HTMLTableElement, but got ${typeof table}.`
        );
    }

    if (typeof selectors !== "object" || selectors === null) {
        throw new Error(
            `Invalid argument: expected an object for selectors, but got ${typeof selectors}.`
        );
    }

    if (selectors.id) {
        table.id = selectors.id;
    }

    if (Array.isArray(selectors.classes)) {
        selectors.classes.forEach((cls) => {
            if (typeof cls === "string") {
                table.classList.add(cls);
            } else {
                warnError("applyTableAttributes", `Skipped non-string class: ${cls}`);
            }
        });
    } else if (selectors.classes !== undefined) {
        warnError(
            "applyTableAtrributes", `selectors.classes must be an array of strings, but got ${typeof selectors.classes}`
        );
    }

    return table;
}


/**
 * Creates a table header (<thead>) with a single row of column headers.
 * 
 * Each string in `columnHeadersList` becomes a <th> element
 * with its `scope` attribute set to "col".
 * 
 * Example:
 *   columnHeadersList = ["Name", "Age", "Email"]
 * 
 * Produces:
 *   <thead>
 *     <tr>
 *       <th scope="col">Name</th>
 *       <th scope="col">Age</th>
 *       <th scope="col">Email</th>
 *     </tr>
 *   </thead>
 *
 * @param {Array<string>} columnHeadersList - Array of column header labels.
 * @returns {HTMLTableSectionElement} The generated <thead> element.
 */
function buildTableHead(columnHeadersList) {

     if (!Array.isArray(columnHeadersList)) {
        throw new Error(
            `Invalid argument: expected an list of strings, but got ${typeof columnHeadersList}.`
        );
    }
    const tableHead = document.createElement("thead");
    const tableRow  = document.createElement("tr");

    columnHeadersList.forEach(columnHead => {
        const thElement       = document.createElement("th");
        thElement.textContent = toTitle(columnHead);
        thElement.scope       = "col";
        tableRow.appendChild(thElement)
    });

    tableHead.appendChild(tableRow);
    return tableHead;
}




/**
 * Builds the body of a table by generating rows (<tr>) and cells (<td>).
 * 
 * The data is defined in the `rowDataList` parameter, which is an array of arrays.
 * Each inner array represents a row, and each element in that inner array
 * represents a cell within that row.
 * 
 * Example:
 *   rowDataList = [
 *     ["col1", "col2", "col3", "col4"],
 *     ["col5", "col6", "col7", "col8"],
 *     ["col9", "col10", "col11", "col12"]
 *   ]
 * 
 * Produces:
 *   <tbody>
 *     <tr>
 *       <td>col1</td><td>col2</td><td>col3</td><td>col4</td>
 *     </tr>
 *     <tr>
 *       <td>col5</td><td>col6</td><td>col7</td><td>col8</td>
 *     </tr>
 *     <tr>
 *       <td>col9</td><td>col10</td><td>col11</td><td>col12</td>
 *     </tr>
 *   </tbody>
 * 
 * @param {Array<Array<*>>} rowDataList - Array of rows, where each row is an array of cell values.
 * @returns {DocumentFragment} A fragment containing the generated table rows and cells.
 */
function buildTableBody(rowsDataList) {

    if (!Array.isArray(rowsDataList)) {
        throw new Error(
            `Invalid argument: expected a list of lists, but got ${typeof rowsDataList}.`
        );
    }
    const tBodyElement = document.createElement("tbody");

    rowsDataList.forEach((colsData) => {

        if (Array.isArray(colsData)) {

            const trElement = document.createElement("tr")

            colsData.forEach((colData) => {
                const tdElement = document.createElement("td");
                tdElement.textContent = colData;
                trElement.appendChild(tdElement);
            })
            tBodyElement.appendChild(trElement);

        } else {
        warnError("buildTableBody", "This is not a an Array  ")
        }
   
})
return tBodyElement;
}


// Test
// const tableHeader  = ["status", "code"]
// const rowsDataList = [["used", "123456789"], ["used", "234567899"], ["used", "9785575215"]]
// const table        = HTMLTableBuilder(tableHeader, rowsDataList)

