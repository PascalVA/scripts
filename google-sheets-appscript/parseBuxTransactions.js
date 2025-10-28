// TODO: Return current asset value from ticker in script

// A mapping of which ticker should be used to
// get the price of an asset
ASSET_TICKER_LOOKUP = {
  "Inbev": "EBR:ABI",
  "Shell": "AMS:SHELL",
  "BMW": "ETR:BMW",
  "Microsoft": "VIE:MSFT",
  "BE Semiconductor": "AMS:BESI",
  "L'Oreal": "ETR:LOR",
  "iShares Core": "S&P 500	AMS:CSPX",
  "Realty Income": "FRA:RY6"
}

function parseBuxTransactions(input_range) {

  // helper function that returns the Cost Average
  // of an asset using First-In-First-Out
  // The cost average does include the trade fee and taxes
  //
  // Returns a mapping of assets and their DCA
  function _dcaFIFO(input_range) {

    /*
       This object holds a chronological list of purchases
       Each entry contains the amount and the total price

       For example:
         {
           "Microsoft": [
              {"qt": 1, "price": 450.00},
              {"qt": 3, "price": 1503.80},
              ...
           ],
           "Realty Income": [{"qt": 1, "price": 48. 01}, {"qt": 1, "price": 59.32}, ...],
           ...
         }
    */
    asset_buckets = {}

    for (row of input_range) {
      transaction_type = row[2]
      transfer_type = row[3]
      price = row[4]
      asset_name = row[8]
      quantity = row[9]

      if (asset_name != '' && !asset_buckets.hasOwnProperty(asset_name)) {
        asset_buckets[asset_name] = []
      }

      if (transaction_type == "Buy Trade" && transfer_type == "CASH_DEBIT") {
        asset_buckets[asset_name].push({ "qt": quantity, "value": Math.abs(price) })
      }

      if (transaction_type == "Sell Trade" && transfer_type == "CASH_CREDIT") {
        while (quantity > 0) {
          if (quantity < asset_buckets[asset_name][0]["qt"]) {
            // If the quantity of the transaction is less than
            // what is in the current bucket, we can simple substract
            // the quantity and continue with the next transaction
            unit_price = asset_buckets[asset_name][0]["value"] / asset_buckets[asset_name][0]["qt"]
            new_quantity = asset_buckets[asset_name][0]["qt"] - quantity
            new_value = new_quantity * unit_price

            asset_buckets[asset_name][0]["qt"] = new_quantity
            asset_buckets[asset_name][0]["value"] = new_value
            quantity = 0
          } else if (quantity == asset_buckets[asset_name][0]["qt"]) {
            // If the quantity is equal to what is in the current bucket
            // We can finish the transaction and remove the bucket
            quantity = 0
            asset_buckets[asset_name].shift()
          } else {
            // If the quantity is greater than what is in the current bucket
            // We can partially resolve the transaction and remove the current bucket
            quantity -= asset_buckets[asset_name][0]["qt"]
            asset_buckets[asset_name].shift()
          }
        }
      }
    }

    // Calculate Cost Average per asset
    dca_mapping = {}
    for (key in asset_buckets) {
      quantity = 0
      value = 0

      for (bucket of asset_buckets[key]) {
        quantity += bucket["qt"]
        value += bucket["value"]
      }

      dca_mapping[key] = Math.round(value / quantity * 100) / 100
    }

    return dca_mapping
  }

  assets = {};
  for (row of input_range) {
    transaction_type = row[2]
    transfer_type = row[3]
    asset_name = row[8]
    quantity = row[9]

    if (asset_name != '' && !assets.hasOwnProperty(asset_name)) {
      assets[asset_name] = 0
    }

    if (transaction_type == "Buy Trade" && transfer_type == "CASH_DEBIT") {
      assets[asset_name] += quantity
    }
    if (transaction_type == "Sell Trade" && transfer_type == "CASH_CREDIT") {
      assets[asset_name] -= quantity
    }
  }

  // get asset DCA
  dca_mapping = _dcaFIFO(input_range)

  // build result 2D Array
  result = []
  for (key in assets) {
    if (assets[key] > 0) {
      result.push([
        key,              // asset name
        "EUR",            // asset currency
        assets[key],      // quantity
        dca_mapping[key]  // Cost Average
      ])
    }
  }

  headers = ["Asset", "Currency", "Amount", "DCA"]
  sorted = result.sort((a, b) => (b[2] * b[3]) - (a[2] * a[3]))  // sort by total value

  return ([headers].concat(sorted))
}
