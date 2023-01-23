import random
from newClasses import Order, OrderBookType, OrderBook
import numpy as np
import pandas as pd
from datetime import datetime
 
depth = 14
 
 
def lamda_cancelation_weighted_sum(lamda_cancellation, ask_or_bid_shares):
    """
    Use np.abs because a or b doesnt matter
    """
 
    return np.dot(lamda_cancellation, np.abs(ask_or_bid_shares[:depth]))
 
 
def draw_new_waiting_time(lam_market, lam_limit, lamda_cancellation_weighted_sum_bid,
                          lamda_cancellation_weighted_sum_ask):
    time_of_event_params = 2 * (lam_market + np.sum(
        lam_limit)) + lamda_cancellation_weighted_sum_bid + lamda_cancellation_weighted_sum_ask
    return float(np.random.exponential(time_of_event_params, size=1))
 
 
def draw_new_event(LAMDA_MRKET, lamda_limit, lamda_cancellation_weighted_sum_ask, lamda_cancellation_weighted_sum_bid):
    actions = np.array(
        [LAMDA_MRKET, LAMDA_MRKET, np.sum(lamda_limit), np.sum(lamda_limit), lamda_cancellation_weighted_sum_ask,
         lamda_cancellation_weighted_sum_bid])
    probability_vector = actions / np.sum(actions)
    return np.random.choice(a=np.arange(0, 6, dtype=int), p=probability_vector)
 
 
def draw_order_volume(params):
    """
    mogen we de lognormal distribution afronden naar een discrete vorm
    :param params:
    :return:
    """
    return int(np.round(np.random.lognormal(params[0], params[1], size=1)))
 
 
def draw_new_order_tick_limit(lam_limit):
    return np.random.choice(np.arange(0, len(lam_limit), dtype=int), p=(lam_limit / np.sum(lam_limit)))
 
 
def draw_new_order_tick_cancellation(lamda_weighted):
    """
    Lamda_weighted depends on bid or ask side, so put in the right Lamda.
    Read the 9th operation of the algorithm in the paper.
    """
    return np.random.choice(np.arange(0, len(lamda_weighted), dtype=int),
                            p=(lamda_weighted / np.sum(np.abs(lamda_weighted))))
 
 
def initialize(orderbook: OrderBook):
    orderbook.add_order(Order(id=1, volume=10), order_type=OrderBookType.BID, order_idx=0)
    orderbook.add_order(Order(id=2, volume=10), order_type=OrderBookType.ASK, order_idx=0)
 
 
def main():
    now = datetime.now()
    orderbook = OrderBook(price=100)
    orderbook.initialize_orderbook()
    N = 10
    INTIIAL_PRICE = 10
    LAM_MARKET = 0.1237
    waiting_time = 0
 
    lam_cancellation = np.array(
        [0.8636, 0.4635, 0.1487, 0.1096, 0.0402, 0.0341, 0.0311, 0.0237, 0.0233, 0.0178, 0.0127, 0.0012, 0.0001,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float
    )[:depth] / 1000
    # lam_cancellation = 0.2 * lam_cancellation
    lam_limit = np.array(
        [0.2842, 0.5255, 0.2971, 0.2307, 0.0826, 0.0682, 0.0631, 0.0481, 0.0462, 0.0321, 0.0178, 0.0015, 0.0001, 0, 0,
         0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float
    )[:depth]
 
    time_log = []
    ask_volume_log = []
    bid_volume_log = []
    price_log = []
 
    bid_reservoir = 250
    ask_reservoir = 250
 
    volume_params_market = (4.0, 1.19)
    volume_params_cancellation = (4.48, 0.82)
    volume_params_limit = (4.47, 0.83)
 
 
    T = 390*60
    print("begin price:", orderbook.price)
 
    for n in range(0, 1000):
 
        lamda_cancellation_weighted_sum_ask = lamda_cancelation_weighted_sum(lam_cancellation,
                                                                             orderbook.get_volume_per_tick(
                                                                                 OrderBookType.ASK))
        lamda_cancellation_weighted_sum_bid = lamda_cancelation_weighted_sum(lam_cancellation,
                                                                             orderbook.get_volume_per_tick(
                                                                                 OrderBookType.BID))
 
        event = draw_new_event(LAM_MARKET, lam_limit, lamda_cancellation_weighted_sum_bid,
                               lamda_cancellation_weighted_sum_ask)
 
        if event == 0:
            """
            Market ask
            """
            volume = draw_order_volume(volume_params_market)
            orderbook.fill_market_order(volume, OrderBookType.ASK)
 
        elif event == 1:
            # "Market bid"
            volume = draw_order_volume(volume_params_market)
            orderbook.fill_market_order(volume, OrderBookType.BID)
 
        elif event == 2:
            # "Limit ask"
            volume = draw_order_volume(volume_params_limit)
            price_tick = draw_new_order_tick_limit(lam_limit)
 
            orderbook.add_order(Order(id=n, volume=volume), OrderBookType.ASK, order_idx=price_tick)
 
        elif event == 3:
            # "Limit bid"
            volume = draw_order_volume(volume_params_limit)
            price_tick = draw_new_order_tick_limit(lam_limit)
 
            orderbook.add_order(Order(id=n, volume=volume), OrderBookType.BID, order_idx=price_tick)
 
        elif event == 4:
            # "cancel ask"
            volume = draw_order_volume(volume_params_cancellation)
            price_tick = draw_new_order_tick_cancellation(
                lam_cancellation * np.abs(orderbook.get_volume_per_tick(OrderBookType.BID))[:depth])
 
            orderbook.cancel_order(idx=price_tick, order_type=OrderBookType.ASK)
 
        elif event == 5:
            # "cancel bid"
            # print("dikke volume", orderbook.get_volume_per_tick(OrderBookType.BID))
            volume = draw_order_volume(volume_params_cancellation)
            price_tick = draw_new_order_tick_cancellation(
                lam_cancellation * np.abs(orderbook.get_volume_per_tick(OrderBookType.BID))[:depth])
 
            orderbook.cancel_order(idx=price_tick, order_type=OrderBookType.BID)
 
        else:
            print('ERROR')
 
        waiting_time += draw_new_waiting_time(LAM_MARKET, lam_limit, lamda_cancellation_weighted_sum_bid,
                                              lamda_cancellation_weighted_sum_ask)
 
        time_log.append(waiting_time)
        ask_volume_log.append(orderbook.get_volume_per_tick(OrderBookType.ASK).tolist())
        bid_volume_log.append(orderbook.get_volume_per_tick(OrderBookType.BID).tolist())
        price_log.append(orderbook.price)
 
    print(time_log)
    print(ask_volume_log)
    print(bid_volume_log)
    print(price_log)
 
    time_log = pd.DataFrame(time_log, columns=['time'])
    ask_volume_log = pd.DataFrame(ask_volume_log)
    bid_volume_log = pd.DataFrame(bid_volume_log)
    price_log = pd.DataFrame(price_log,columns=['price'])
 
 
 
 
    data = pd.concat([time_log, price_log,ask_volume_log,bid_volume_log],axis = 1)
 
    # data = pd.DataFrame([np.array(time_log), np.array(price_log), np.array(ask_volume_log), np.array(bid_volume_log)], columns=['time_log', 'price_log', 'ask_volume_log', 'bid_volume_log'])
 
    data.to_csv(f'data/orderbooklog_with_vols.csv')
    # print("volume of orderbook asks:", orderbook.get_volume_per_tick(OrderBookType.ASK))
    # print("and the normal volume", orderbook.asks.get_orderbook_side_volume())
    # print("volume of orderbook bids:", orderbook.get_volume_per_tick(OrderBookType.BID))
    print("end price:", orderbook.price)
 
    # best_bid_ask()
    # lamda_weighted_sum_cancellations_ask = compute_weighted_sum_of_shares_at_price_levels()
    # lamda_weighted_sum_cancellations_bid = compute_weighted_sum_of_shares_at_price_levels()
 
 
if __name__ == '__main__':
    main()