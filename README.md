# Concurrency Control Protocol

## Description

This repository is a project for simulations of database concurrency control in Python language. The protocols implemented in this project are Two-Phase Locking Protocol and Optimistic Concurrency Control.

## Requirements

- Python 3

## How to run

### Two-Phase Locking protocol

1. Navigate to the directory of the project
2. Run the following command

   ```
   python3 2PL.py
   ```

3. Insert an input string of the query you would like to try. Example of format with ';' as delimitter is as such:

   ```
   R1(X); R2(Y); R1(Y); R2(X); C1; C2;
   ```


### OCC
1. Navigate to the directory of the project
2. Run the following command

   ```
   python3 occmain.py
   ```
3. Insert an input file name with the sequence of input string query. Here is an example of input:
   ```
   test.txt
   ```

   Here is the example of inside the file:
   ```
   R1(X)
   W2(X)
   R1(Y)
   W2(Y)
   C1
   C2
   ```
