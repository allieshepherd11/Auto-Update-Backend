

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("inputVar").addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent the default form submission


        var numMonths = parseFloat(document.getElementById("numMonths").value);
        var time = Array.from({length: numMonths + 1}, (_, i) => i); 

        var qi = parseFloat(document.getElementById("qi").value);
        var Di = parseFloat(document.getElementById("Di").value);
        var b = parseFloat(document.getElementById("b").value);
        var oilPrice = parseFloat(document.getElementById("oilPrice").value);
        var netInterest = parseFloat(document.getElementById("netInterest").value);
        var taxRate = parseFloat(document.getElementById("taxRate").value);
        var intRate = parseFloat(document.getElementById("intRate").value) / 100;
        var drillCost = parseFloat(document.getElementById("drillCost").value);


        const hyperRate =[]
        var limitedTime = []
        const pvArray = []
        const revs = []
        for (let t of time) {
            let yVal = qi*Math.pow((1+b*Di*t), (-1/b))
            hyperRate.push(yVal)
            const rev = yVal*oilPrice*netInterest*taxRate
            revs.push(rev)
            pvArray.push(rev*Math.pow(1+intRate/12,-(t+1)))

            limitedTime.push(t);
            if (yVal < 130){
                console.log("hit economic limit", t);
                alert(`Bopm goes under 130 after ${t} months`)
                break;
            }
        }
        const pv = pvArray.reduce((acc, val) => acc + val, 0);

        var eur = 0 
        for (let y of hyperRate) {
            eur += y
        }
        console.log('eur', eur)

        document.getElementById("eur").innerText = `EUR: ${parseFloat(eur.toFixed(1))}`;

        let traceHyperRate = makeTrace(
            time,
            hyperRate,
            "Total Fluid",
            null,
            "green"
        );

        var layout = {
            title: "Hyperbolic Curve",
            xaxis: {
              showline: true,
              gridcolor: '#dbdbdb',
              type: 'linear'
            },
            yaxis: {
              range: [0, null],
              type: 'linear', 
              tickvals: 'auto',
              ticktext: 'auto',
              showline: true,
              gridcolor: '#dbdbdb',
            },
            legend: {
              bgcolor: 'rgba(0, 0, 0, 0)',
              font: {
                  color: '#000000'
              },
              orientation: "h",
                  y: 1.1,
                  xanchor: window.innerWidth > 600 ? "center" : "left",
                  x: .5,
          },
        }


        Plotly.newPlot("hyperbolicRateCurve", [traceHyperRate], layout, config);
        let presentValueArray = [];
        var presentValue = 0;
        
        for (let t in limitedTime) {
            let monthFV = hyperRate[t]*oilPrice*netInterest*taxRate
            let monthPV = monthFV/Math.pow(1 + (intRate / 12), (parseInt(t)+1));
            presentValueArray.push(monthPV);
            presentValue += monthPV
        }
        console.log('presentValueArray', presentValueArray)
        document.getElementById("presentValue").innerText = `Present Value: ${parseFloat(presentValue.toFixed(2))}`;

        revs.unshift(-drillCost)
        let irr = ((solve(revs) - 1)*12*100).toFixed(1)
        console.log('irr', irr)
        document.getElementById("irr").innerText = `Internal Rate of Return (IRR): ${irr}%`;


        let nominalValue = eur*oilPrice*netInterest*taxRate
        document.getElementById("NominalValue").innerText = `Nominal Value: ${parseFloat(nominalValue.toFixed(2))}`;



   
'use strict';


function newtonRaphson (f, fp, x0, options) {
  var x1, y, yp, tol, maxIter, iter, yph, ymh, yp2h, ym2h, h, hr, verbose, eps;

  // Iterpret variadic forms:
  if (typeof fp !== 'function') {
    options = x0;
    x0 = fp;
    fp = null;
  }

  options = options || {};
  tol = options.tolerance === undefined ? 1e-7 : options.tolerance;
  eps = options.epsilon === undefined ? 2.220446049250313e-16 : options.epsilon;
  maxIter = options.maxIterations === undefined ? 20 : options.maxIterations;
  h = options.h === undefined ? 1e-4 : options.h;
  verbose = options.verbose === undefined ? false : options.verbose;
  hr = 1 / h;

  iter = 0;
  while (iter++ < maxIter) {
    y = f(x0);

    if (fp) {
      yp = fp(x0);
    } else {
      yph = f(x0 + h);
      ymh = f(x0 - h);
      yp2h = f(x0 + 2 * h);
      ym2h = f(x0 - 2 * h);

      yp = ((ym2h - yp2h) + 8 * (yph - ymh)) * hr / 12;
    }

    // Check for badly conditioned update (extremely small first deriv relative to function):
    if (Math.abs(yp) <= eps * Math.abs(y)) {
      if (verbose) {
        console.log('Newton-Raphson: failed to converged due to nearly zero first derivative');
      }
      return false;
    }

    // Update the guess:
    x1 = x0 - y / yp;

    // Check for convergence:
    if (Math.abs(x1 - x0) <= tol * Math.abs(x1)) {
      if (verbose) {
        console.log('Newton-Raphson: converged to x = ' + x1 + ' after ' + iter + ' iterations');
      }
      return x1;
    }

    x0 = x1;
  }

  if (verbose) {
    console.log('Newton-Raphson: Maximum iterations reached (' + maxIter + ')');
  }

  return false;
}


function solve(cfs){
    console.log('cfs', cfs)
    console.log('cfs', typeof(cfs[0]))
    console.log('cfs', typeof(cfs[5]))


    const f = (x) => cfs.reduce((s, cf, idx) => s + parseInt(cf) * Math.pow(x, -idx), 0);
    const fPrime = (x) => cfs.reduce((s, cf, idx) => s + -idx * parseInt(cf) * Math.pow(x, -idx - 1), 0);



    const root = newtonRaphson(f,fPrime,1);
    console.log('root', root)

    return root;

}

    });
});

const makeTrace = (x, y, name, type="lines", color, text, visible=true, dash) => ({
    x,
    y,
    text,
    name,
    visible,
    line: {
        color,
        dash
    },
    mode: type
});

const config = {
    modeBarButtonsToRemove: [
        "sendDataToCloud",
        "autoScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "toggleSpikelines",
    ],
    displaylogo: false,
    responsive: true,
    displayModeBar: false,
    responsiveConfig: [
        {
        // Mobile devices with width less than or equal to 768px
        breakpoint: 768,
        options: {
            legend: { orientation: 'h', y: -0.2 }
        }
        },
        {
        // Desktop devices with width greater than 768px
        breakpoint: 0,
        options: {
            legend: { orientation: 'v', y: 1 }
        }
        }
    ]
};