import re

class Operation():
    def __init__(self, transaction, action, resource):
        # Construction example Operation (TX, R/W/C, X/Y/etc)
        self.transaction = transaction
        self.action = action
        self.resource = resource

    def format(self, wait=False):
        if not self.resource:
            return '%s%s' % (self.action, self.transaction)
        return '%s%s(%s)' % (self.action, self.transaction, self.resource)

    def is_write(self):
        return self.action == 'W'

    def is_read(self):
        return self.action == 'R'

    def is_commit(self):
        return self.action == 'C'
    


class Transaction():
    is_growing = True

    def __init__(self, value):
        self.value = value


class Lock():
    def __init__(self, transaction, exclusive, resource, released=False):
        self.transaction = transaction
        self.exclusive = exclusive
        self.resource = resource
        self.released = released

    def format(self):
        # Formatting for output result
        operation = 'L' if not self.released else 'U'
        lock_type = 'X' if self.exclusive else 'S'
        return '%s%s%s(%s)' % (operation, lock_type, self.transaction, self.resource)


class TwoPhaseLocking():
    
    def execute(self, input):
        self.operations = []
        self.wait_operations = []
        self.transactions = {}
        self.locks = []
        self.execution_list = []
        self.final_schedule = []
        self.counter = 0

        self.parse(input)
        print(f'Input query: {(input)}')
        self.run()
        print()

    def parse(self, input):
        substrings = re.split(r';\s*', input)
        for substring in substrings:
            sre_match = None
            # Adding operation based on each input action
            if re.match(r'r(\d+)\(([a-zA-Z]+)\)', substring, re.IGNORECASE):
                sre_match = re.match(r'r(\d+)\(([a-zA-Z]+)\)', substring, re.IGNORECASE)
                # Adding operation read
                self.operations.append(Operation(sre_match.group(1), 'R',sre_match.group(2)))
            elif re.match(r'w(\d+)\(([a-zA-Z]+)\)', substring, re.IGNORECASE):
                sre_match = re.match(r'w(\d+)\(([a-zA-Z]+)\)', substring, re.IGNORECASE)
                # Adding operation write
                self.operations.append(Operation(sre_match.group(1), 'W',sre_match.group(2)))
            elif re.match(r'c(\d+)', substring, re.IGNORECASE):
                sre_match = re.match(r'c(\d+)', substring, re.IGNORECASE)
                # Adding operation commit, doesnt have resource
                self.operations.append(Operation(sre_match.group(1), 'C', None))
            else:
                raise Exception('Invalid input')
            # Adding new transactions into transaction list
            if sre_match.group(1) not in self.transactions.keys():
                self.transactions[str(sre_match.group(1))] = Transaction(sre_match.group(1))

    def print_result(self):
        operations_text = ''
        for item in self.final_schedule:
            if isinstance(item, Operation) or isinstance(item, Lock):
                operations_text += '%s; ' % (item.format())
        if operations_text:
            print('Schedule Akhir:', operations_text.rstrip('; '))

    def has_lock(self, operation):
        for lock in self.locks:
            if lock.resource == operation.resource and lock.transaction == operation.transaction:
                if (lock.exclusive and operation.action == 'W') or (not lock.exclusive and operation.action == 'R'):
                    return True
        return False

    def can_lock(self, operation):
        relevant_locks = []
        # Collect relevant locks for the given resource
        for lock in self.locks:
            if lock.resource == operation.resource:
                relevant_locks.append(lock)
                
        # Check conditions for acquiring the lock
        for lock in relevant_locks:
            if not lock.exclusive:
                if lock.transaction == operation.transaction and len(relevant_locks) == 1 and operation.action == 'W':
                    return True
                elif lock.transaction != operation.transaction and operation.action == 'R':
                    return True
            # If none of the conditions are met, return False
            return False
        return True


    def add_lock(self, operation):
        if operation.action == 'W':
            exclusive = True
        else:
            exclusive = False
        lock = Lock(operation.transaction, exclusive, operation.resource)
        self.locks.append(lock)
        self.final_schedule.append(lock)


    # def release_locks(self, transaction):
    #     original_locks = list(self.locks)
    #     self.locks[:] = [lock for lock in self.locks\
    #         if not lock.transaction == transaction]
    #     for released_lock in set(original_locks).difference(set(self.locks)):
    #         lock = Lock(released_lock.transaction, released_lock.exclusive, released_lock.resource, True)
    #         self.final_schedule.append(lock)
    def release_locks(self, transaction):
        original_locks = list(self.locks)

        updated_locks = []
        # Collecting locks that has been released (locks outside self.locks)
        released_locks = set(original_locks).difference(set(self.locks))
        # Releasing all locks related to transaction (after commit)
        for lock in self.locks:
            if lock.transaction != transaction:
                updated_locks.append(lock)
            else:
                released_locks.add(lock)

        self.locks = updated_locks

        for released_lock in released_locks:
            lock = Lock(released_lock.transaction, released_lock.exclusive, released_lock.resource, True)
            self.final_schedule.append(lock)


    def has_deadlock(self):
        conflicts = []
        for wait_operation in self.wait_operations:
            for lock in self.locks:
                if wait_operation.transaction != lock.transaction and\
                    wait_operation.resource == lock.resource:
                        conflicts.append((wait_operation.transaction,
                            lock.transaction))
        conflicts_copy = list(conflicts)
        for conflict in conflicts:
            for conflict_copy in conflicts_copy:
                if conflict[0] == conflict_copy[1] and\
                    conflict[1] == conflict_copy[0]:
                    return conflict
        return False
        
    def abort(self, transaction):
        # Remove wait operations related to the transaction
        updated_wait_operations = [wait_op for wait_op in self.wait_operations if wait_op.transaction != transaction]
        self.wait_operations = updated_wait_operations

        # Add an "Abort" action for the aborted transaction in the final schedule
        abort_action = Operation(transaction, 'A', None)
        self.final_schedule.append(abort_action)
        
        # Release locks before removing
        self.release_locks(transaction)

        # Remove locks held by the transaction
        updated_locks = [lock for lock in self.locks if lock.transaction != transaction]
        self.locks = updated_locks

        # Adjust counter and execution list
        count = 0
        updated_execution_list = []
        for index, operation in enumerate(self.execution_list):
            if operation.transaction == transaction and index <= self.counter:
                count += 1
            elif operation.transaction != transaction:
                updated_execution_list.append(operation)
        self.execution_list = updated_execution_list
        self.counter -= count

        # Add original operations of the aborted transaction back to execution list
        for operation in self.operations:
            if operation.transaction == transaction:
                self.execution_list.append(operation)

        print(f'A deadlock was found. The transaction {transaction} was aborted.')

    def can_commit(self, transaction):
        pending_operations = []
        for operation in self.wait_operations:
            if operation.transaction == transaction:
                pending_operations.append(operation)
        return len(pending_operations) == 0

    def run_operation(self, operation):
        if operation.is_write() or operation.is_read():
            if self.transactions[str(operation.transaction)].is_growing:
                if self.has_lock(operation):
                    self.final_schedule.append(operation)
                elif self.can_lock(operation):
                    self.add_lock(operation)
                    self.final_schedule.append(operation)
                else:
                    return operation
            else:
                print(f'Operation {operation.format()} because it is already shrinking phase')
        elif operation.is_commit():
            if self.can_commit(operation.transaction):
                self.final_schedule.append(operation)
                self.release_locks(operation.transaction)
                self.transactions[operation.transaction].is_growing = False

    def run(self):
        self.execution_list = list(self.operations)
        while self.counter < len(self.execution_list):
            # If Older transactions have used lock exlusively, other transaction operation put in wait.
            if any(operation.transaction == self.execution_list[self.counter].transaction and not self.execution_list[self.counter].is_commit() for operation in self.wait_operations):
                self.wait_operations.append(self.execution_list[self.counter])
                print(f'Operation {(self.execution_list[self.counter].format())} put in wait.')
            # If operation is scheduleable.
            else:
                # Scheduliing all operations and checking for deadlock
                operation = self.run_operation(self.execution_list[self.counter])
                if operation and not operation.is_commit():
                    self.wait_operations.append(operation)
                    print(f'Operation {(operation.format())} put in wait.')
                    deadlock = self.has_deadlock()
                    if deadlock:
                        self.abort(operation.transaction)
                # Running operations in order that is queued in the waiting list.
                self.run_wait_operations()
            self.counter += 1
            if self.counter == len(self.execution_list):
                for wait_operation in self.wait_operations:
                    self.execution_list.append(wait_operation)
                # Empty out wait operations, put in execution list
                self.wait_operations = []
        # Reset counter
        self.counter = 0
        # Final schedule result printed and showed
        self.print_result()
        
    def run_wait_operations(self):
        if self.wait_operations:
            rewait_operations = []
            for wait_operation in self.wait_operations:
                rewait_operation = self.run_operation(wait_operation)
                if rewait_operation and not rewait_operation.is_commit():
                    rewait_operations.append(rewait_operation)
                    deadlock = self.has_deadlock()
                    if deadlock:
                        self.abort(rewait_operation.transaction)
            self.wait_operations = rewait_operations


if __name__ == '__main__':
    TwoPL = TwoPhaseLocking()
    input = input("Enter input operations string (delimitter with ;): ")
    TwoPL.execute(input)


    
    
