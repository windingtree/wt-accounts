$(document).ready(function() {

    $(".ethstat").hover(function() {
        if ($(window).width() < 736) {
            //$(".statschartcontainer").before($(".ico-eth"));
            $(".lifdetails").slideUp();
            $(".mvmdetails").slideUp();
            $(".ethdetails").css("display", "block").hide().slideDown();
        } else {
            $(".ethdetails").css("display", "flex").hide().slideDown();
        }
    }, function() {
        $(".ethdetails").slideUp();
    });

    $(".lifstat").hover(function() {
        if ($(window).width() < 736) {
            $(".ethdetails").slideUp();
            $(".mvmdetails").slideUp();
            $(".lifdetails").css("display", "block").hide().slideDown();
        } else {
            $(".lifdetails").css("display", "flex").hide().slideDown();
        }
    }, function() {
        $(".lifdetails").slideUp();
    });

    $(".mvmstat").hover(function() {
        if ($(window).width() < 736) {
            $(".ethdetails").slideUp();
            $(".lifdetails").slideUp();
            $(".mvmdetails").css("display", "block").hide().slideDown();
        } else {
            $(".mvmdetails").css("display", "flex").hide().slideDown();
        }
    }, function() {
        $(".mvmdetails").slideUp();
    });


    /*Chart.plugins.register({
    beforeDraw: function(chart) {


          var data = chart.data.datasets[0].data;
          var sum = data.reduce(function(a, b) {
              return a + b;
          }, 0);
          var width = chart.chart.width,
              height = chart.chart.height,
              ctx = chart.chart.ctx;
          ctx.restore();
          ctx.fillStyle = "#fff";
          var fontSize = (height / 6).toFixed(2);
          ctx.font = "300 " + fontSize + "px Source Sans Pro";
          ctx.textBaseline = "middle";

            var text = '',
                textX = Math.round((width - ctx.measureText(text).width) / 2),
                textY = height / 2;

          ctx.fillText(text, textX, textY);
          ctx.save();

    }
    });
*/


    var ctx = document.getElementById('statschart').getContext('2d');
    var myDoughnutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['pre-ICO', 'ICO'],
            datasets: [{
                backgroundColor: ['#FAF3DD', '#BCFFDB'],
                borderColor: 'transparent',
                data: [15, 85],
                datalabels: {
                    color: ['#FAF3DD', '#BCFFDB'],
                    align: 'end',
                    font: {
                        size: '16',
                        family: 'Source Sans Pro'
                    },
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }
            }]
        },
        options: {
            rotation: -3,
            legend: {
                display: false,
            },
            cutoutPercentage: 95,


            tooltips: {
                callbacks: {
                    title: function(tooltipItem, data) {
                        return data['labels'][tooltipItem[0]['index']];
                    },
                    label: function(tooltipItem, data) {
                        return data['datasets'][0]['data'][tooltipItem['index']] + ' % of all contributed ETH';
                    },
                },
                backgroundColor: '#FFF',
                titleFontSize: 16,
                titleFontColor: '#0066ff',
                bodyFontColor: '#000',
                bodyFontSize: 14,
                displayColors: false
            }


        },
        circumference: 1

    });

    var ctx2 = document.getElementById('lifschart').getContext('2d');
    var LifChart = new Chart(ctx2, {
        type: 'pie',
        data: {
            labels: ['Lifs for Backers', 'Lifs for Project Funding'],
            datasets: [{
                backgroundColor: ['#FAF3DD', '#BDADEA'],
                borderColor: 'transparent',
                data: [75, 25],
                datalabels: {
                    color: ['#FAF3DD', '#BDADEA'],
                    align: 'end',
                    font: {
                        size: '16',
                        family: 'Source Sans Pro'
                    },
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }

            }]
        },
        options: {
            rotation: -5,
            legend: {
                display: false,
            },
            cutoutPercentage: 95,

            tooltips: {
                callbacks: {
                    title: function(tooltipItem, data) {
                        return data['labels'][tooltipItem[0]['index']];
                    },
                    label: function(tooltipItem, data) {
                        return data['datasets'][0]['data'][tooltipItem['index']] + ' % of all generated Lífs';
                    },
                },
                backgroundColor: '#FFF',
                titleFontSize: 16,
                titleFontColor: '#0066ff',
                bodyFontColor: '#000',
                bodyFontSize: 14,
                displayColors: false
            }
        },

    });


    var ctx3 = document.getElementById('mvmchart').getContext('2d');
    var mvmChart = new Chart(ctx3, {
        type: 'pie',
        data: {
            labels: ['ETH for project funding', 'ETH for MVM'],
            datasets: [{
                backgroundColor: ['#FAF3DD', '#533745'],
                borderColor: 'transparent',
                data: [68, 32],
                datalabels: {
                    color: ['#FAF3DD', '#533745'],
                    align: 'end',
                    font: {
                        size: '16',
                        family: 'Source Sans Pro'
                    },
                    formatter: function(value, context) {
                        return value + '%';
                    }
                }

            }]
        },
        options: {
            rotation: -5,
            legend: {
                display: false,
            },
            cutoutPercentage: 95,
            tooltips: {
                callbacks: {
                    title: function(tooltipItem, data) {
                        return data['labels'][tooltipItem[0]['index']];
                    },
                    label: function(tooltipItem, data) {
                        return data['datasets'][0]['data'][tooltipItem['index']] + ' % of all contributed ETH';
                    },
                },
                backgroundColor: '#FFF',
                titleFontSize: 16,
                titleFontColor: '#0066ff',
                bodyFontColor: '#000',
                bodyFontSize: 14,
                displayColors: false
            }
        },


    });


});





// TGE Scripts
var SOFT_CAP = 4350;
var MAX_CAP = (10 - 1.5) * 1000000 / 1150; // Our max cap is $10M, we've already had $1.5 from the presale; $1150 is the hardcoded ETH rate
var icoAddress = "0x9df3a24d738ae98dea766cd89c3aef16583a4daf";
var tokenAddress = "0xeb9951021698b42e4399f9cbb6267aa35f82d59d";
var contributorAddress = userAddress;
var maxUnverifiedContribution = 15;

// Get total ETH raised in wei unit, returns promise
function getEthSent(contributor) {
    var params = $.param({
        module: 'proxy',
        action: 'eth_call',
        tag: 'latest',
        to: icoAddress,
        data: '0x842a77d3000000000000000000000000' + contributor.substring(2),
        apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
    });
    return $.get('https://api.etherscan.io/api?' + params);
}

// Get total supply of Lif, returns promise
function getLifBalance(contributor) {
    var params = $.param({
        module: 'proxy',
        action: 'eth_call',
        tag: 'latest',
        to: tokenAddress,
        data: '0x70a08231000000000000000000000000' + contributor.substring(2),
        apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
    });
    return $.get('https://api.etherscan.io/api?' + params);
}

// Refresh TGE values
function refreshUserContribution() {
    if (icoAddress != "0x0000000000000000000000000000000000000000")
        getEthSent(contributorAddress).then(function(weiSent) {
            var ETHSent = (Number(weiSent.result) / 1e18);
            console.log('ETH Sent:', ETHSent);

            // Show only profile verification if contribution more than maxUnverifiedContribution
            if (ETHSent >= maxUnverifiedContribution && verifiedUser) {
                $('#verification-status').show();
                $('#proof-of-address-input').show();
                $('#verify-profile').show();
                $('#verify-alert').show();
            }
            $('#totalETHSent').text(parseFloat(ETHSent).toLocaleString('en') + ' ETH');
        });
    else
        $('#totalETHSent').text('0 ETH')

    if (tokenAddress != "0x0000000000000000000000000000000000000000")
        getLifBalance(contributorAddress).then(function(balance) {
            var libBalance = (Number(balance.result) / 1e18);
            console.log('Lif Balance:', balance);
            $('#totalLifBalance').text(parseFloat(libBalance).toLocaleString('en') + ' LIFs');
        });
    else
        $$('#totalLifBalance').text('0 LIFs');
}

// Check everything every 10 seconds
refreshUserContribution();
