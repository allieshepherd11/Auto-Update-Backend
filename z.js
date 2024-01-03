import { monitorRegion } from "./modules/region";
import { select, json } from "d3";

function createAnalysis(data) {
  

  function buildTable(tableData) {
    const tbodyFluid = select("tbody#table-no-fluids");
    const tbodyOil = select("tbody#table-no-oil");
    const tbodyMa = select("tbody#table-low-ma");

    tbodyFluid.html("");
    tbodyOil.html("");
    tbodyMa.html("");

    const data = tableData.map(
      ([
        well,
        date,
        oil,
        gas,
        water,
        tp,
        cp,
        comms,
        ,
        fluid,
        ma7dOil,
        ,
        ma30Oil,
        maRatio,
        condtion,
      ]) => [
        well,
        new Date(date).toISOString().split('T')[0].slice(5),
        oil.toFixed(0),
        gas.toFixed(0),
        water.toFixed(0),
        fluid.toFixed(0),
        tp,
        cp,
        comms,
        ma7dOil.toFixed(2),
        ma30Oil.toFixed(2),
        maRatio.toFixed(2),
        condtion,
      ]
    );

    data.forEach((well) => {
      let row;
      const conditions = well[well.length-1]
      if (conditions.includes("No Fluids")) row = tbodyFluid.append('tr')
      else if (conditions.includes("No Oil")) row = tbodyOil.append('tr')
      else if (conditions.includes("Low MA Oil")) row = tbodyMa.append('tr')

      for (let i = 0; i < well.length; i++) {
        let cell = row.append("td");
        cell.text(well[i]);
      }
    });
  }

  $(document).ready(function () {
    $("tr td:nth-child(1)").each(function () {
      $(this).html('<a href="./curves.html">' + $(this).text() + "</a>");
      $(this).click(function () {
        sessionStorage.setItem("siteSelection", $(this).text());
      });
    });
  });

  buildTable(data);
}

$(document).ready(function () {
  $("#header").load("../src/pages/header.html", () => {
    monitorRegion();
  });
});

let region = sessionStorage.region;

let data = null;
if (region == "ST")
  data = await json("../data/ST/analyzeST.json").then((data) => {
    return data;
  });
console.log('data', data)
createAnalysis(data);
