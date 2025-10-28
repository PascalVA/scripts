// TODO: This script should be changed and merged with the parseBuxTransactions script.
//       It should also handle the logic of printing the asset, fiat and amount fields.
//
// This script parses the transactions for specific exchanges and calculates the
// DCA of remaining assets using FIFO (First-In First-Out)
//
// Usage:
//   =dcaFIFO(RANGE, EXCHANGE)
//
// Example:
//   =dcaFIFO(A2:O, "bitvavo")


// represents a single transaction
class Transaction {

  constructor(row, exchange) {
    this["_load_row_" + exchange.toLowerCase()](row);
  }

  // parse rows for bitvavo exchange
  _load_row_bitvavo(row) {
    this.date = this._parse_date(row[1], row[2]);
    this.asset = row[4];
    this.amount = Math.abs(row[5]);
    this.type = row[3].toLowerCase();
    this.total_price = Math.abs(row[9]);  // Total price includes the fee
  }

  // build non-standard date split over two columns when testing
  _parse_date(date, time) {
    if (typeof (date) === "string") {
      var [year, month, day] = date.split("-");
      date = new Date(year, month, day);
    }

    if (typeof (time) === "string") {
      var [hours, minutes, temp] = time.split(":");
      if (temp) {
        var [seconds, milliseconds] = temp.split(".");
      } else {
        [seconds, milliseconds] = [0, 0];
      }
      if (milliseconds == undefined) {
        milliseconds = 0;
      }
    } else {
      var hours = time.getHours();
      var minutes = time.getMinutes();
      var seconds = time.getSeconds();
      var milliseconds = time.getMilliseconds();
    }

    return new Date(date.getFullYear(), date.getMonth(), date.getDate(), hours, minutes, seconds, milliseconds);
  }
}

// return First-In-First-Out DCA given a list of transactions
function dcaFIFO(input, exchange) {

  // group transactions by asset
  var transactions_by_asset = {};
  for (i in input) {

    // skip empty rows
    if (input[i][0] == "") {
      continue;
    }

    // parse transaction
    transaction = new Transaction(input[i], exchange);

    // skip fiat
    if (transaction.asset == "EUR") {
      continue;
    }

    if (!transactions_by_asset.hasOwnProperty(transaction.asset)) {
      transactions_by_asset[transaction.asset] = [];
    }

    transactions_by_asset[transaction.asset].push(transaction);
  }

  // calculate DCA for each asset using FIFO
  dca_by_asset = [];
  for (i in transactions_by_asset) {

    // sort transactions by date ascending
    transactions_by_asset[i].sort(function (a, b) {
      return a.date - b.date;
    })

    // calculate DCA using FIFO
    var queue = [];
    for (transaction_index in transactions_by_asset[i]) {

      transaction = transactions_by_asset[i][transaction_index];

      if (transaction.type === "buy") {
        // add bucket to FIFO queue
        queue.push({
          amount: transaction.amount,
          total_price: transaction.total_price
        });
      } else if (transaction.type === "staking" || transaction.type === "deposit" || transaction.type == "manually_assigned") {
        // deposits, staking and manually assigned don't have a price associated
        queue.push({
          amount: transaction.amount,
          total_price: 0
        });
      } else if (transaction.type === "sell") {
        // HACK: If transaction is below 0.0000001, consider the transaction as resolved
        while (transaction.amount > 0.00001) {
          Logger.log("transaction.amount: " + transaction.amount + ", asset: " + i + ", queue: " + JSON.stringify(queue, null, 2))
          if (queue[0].amount < transaction.amount) {
            // the queue record only partially covers the sale or withdrawal transaction amount
            // we substract the queue amount and continue processing this transaction
            transaction.amount = transaction.amount - queue[0].amount;
            queue.shift();
          } else if (queue[0].amount == transaction.amount) {
            // the queue record amount and transaction amount are equal
            // we can remove the queue record and continue with the next transaction
            queue.shift();
            break;
          } else {
            // the queue record has a larger amount than the transaction amount
            // we have to update the queue record and can continue with the next transaction
            new_amount = queue[0].amount - transaction.amount;
            new_total_price = new_amount * (queue[0].total_price / queue[0].amount);
            queue[0].amount = new_amount;
            queue[0].total_price = new_total_price;
            break;
          }
        }
      }
    }

    // now we calculate the DCA of the remaining queue records
    amount = 0;
    value = 0;
    for (record_index in queue) {
      amount = amount + queue[record_index].amount;
      value = value + queue[record_index].total_price;
    }

    if (amount > 0.00000001) {
      // round to two decimal points
      dca_by_asset.push([i, Math.round(value / amount * 100) / 100]);
    }
  }

  return (dca_by_asset);
}
