# CoShare.jp ✈️
**Flight price comparison app focused on codeshare route detection**  
コードシェア便の価格差を検出する、日本向けフライト比較Webアプリ

---

## Overview / 概要

**EN:**  
CoShare.jp detects price gaps between codeshare flights — the same physical
flight sold under different airline codes at different prices.
Built as a graduation project at Kyoto Seika University.

**JP:**  
同じ物理フライトが異なる航空会社コードで異なる価格で販売される
「コードシェア便」の価格差を検出するWebアプリです。
京都精華大学の卒業制作として個人開発しています。

---

## Tech Stack / 技術スタック

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, REST API |
| Frontend | React, JavaScript, CSS |
| Database | PostgreSQL (Neon) |
| Deployment | Vercel (Serverless Functions) |
| External APIs | Amadeus Flight API, Google Places API |

---

## Features / 主な機能

- Codeshare price gap detection / コードシェア価格差の検出
- Flight search with flexible dates / 柔軟な日程でのフライト検索
- Annual price trend analysis / 年間価格トレンド分析
- Destination recommendations / 目的地レコメンド
- Holiday detection (Japan) / 日本の祝日検出

---

## Background / 開発背景

**EN:**  
Inspired by a personal family experience where the same flight was found
at significantly different prices depending on the booking airline code.

**JP:**  
家族が同じフライトをコードシェアの違いで大幅に異なる価格で購入した
実体験をきっかけに開発を始めました。

---

## Architecture / アーキテクチャ

- 5 REST API endpoints deployed as Vercel Serverless Functions
- Neon PostgreSQL for flight data persistence
- React frontend (currently in development / フロントエンド開発中)

---

## Status / 開発状況

- ✅ Backend complete / バックエンド完成
- 🚧 Frontend in progress / フロントエンド開発中
- ⏳ Deployment coming soon / デプロイ準備中

---

## Author / 作者

Gabriel Harada Dias  
Kyoto Seika University, 2027 graduation  
GitHub: [@nosfer4tu](https://github.com/nosfer4tu)