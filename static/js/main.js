// TGE Scripts
var SOFT_CAP = 4350;
var icoAddress = "0x9df3a24d738ae98dea766cd89c3aef16583a4daf";
var tokenAddress = "0xeb9951021698b42e4399f9cbb6267aa35f82d59d";
var contributorAddress = userAddress;
var maxUnverifiedContribution = 15;

//Set addresses
$('#userAddress').text(contributorAddress.toString());

// Get total ETH raised in wei unit, returns promise
function getEthSent(contributor) {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: icoAddress,
      data: '0x842a77d3000000000000000000000000'+contributor.substring(2),
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
      data: '0x70a08231000000000000000000000000'+contributor.substring(2),
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Get total ETH raised in wei unit, returns promise
function getWeiRaised() {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: icoAddress,
      data: '0x4042b66f',
      apikey: '5FUHMWGH51JT3G9EARU4K4QH3SVWYIMFIB',
  });
  return $.get('https://api.etherscan.io/api?' + params);
}

// Get total supply of Lif, returns promise
function getTotalLif() {
  var params = $.param({
      module: 'proxy',
      action: 'eth_call',
      tag: 'latest',
      to: tokenAddress,
      data: '0x18160ddd',
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

function setEthRaised(eth_raised) {
  var bar_end = eth_raised * 1.2;
  var soft_cap_percent = Math.round(SOFT_CAP / bar_end * 100);
  var above_soft_percent = Math.round((eth_raised - SOFT_CAP) / bar_end * 100);

  $('#beforeCapBar').css({
      width: soft_cap_percent + '%',
      opacity: 1,
  });
  $('#beforeCapBarRest').css({
      width: '0',
      opacity: 1,
  });
  $('#afterCapBar').css({
      width: above_soft_percent + '%',
      opacity: 1,
  });
  $('#afterCapBarRest').css({
      width: 100-above_soft_percent-soft_cap_percent + '%',
      opacity: 1,
  });
  $('#afterCapBar').text(eth_raised.toLocaleString('en') + ' ETH');

  $('#ethRaised').text(parseFloat(eth_raised).toLocaleString('en'));
  $('#progressBar').text(parseFloat(eth_raised).toLocaleString('en') +' ETH');
}

// Refresh TGE values
function refreshTGEValues() {
    if (icoAddress != "0x0000000000000000000000000000000000000000")
      getWeiRaised().then(function(weiRaised) {
        var icoETHRaised = (Number(weiRaised.result) / 1e18);
        console.log('ETH TGE raised:', icoETHRaised)
        setEthRaised(icoETHRaised);
      });

    if (tokenAddress != "0x0000000000000000000000000000000000000000") {
      getTotalLif().then(function(totalSupply) {
        var lifTotalSupply = (Number(totalSupply.result) / 1e18) * 4/3;
        $('#totalLif').text(parseFloat(lifTotalSupply).toLocaleString('en'))
      });
    } else {
      $('#totalLif').text(parseFloat(lifTotalSupply).toLocaleString('en'))
    }
}

// Check everything every 10 seconds
refreshTGEValues();
setInterval(refreshTGEValues, 1000*10);
