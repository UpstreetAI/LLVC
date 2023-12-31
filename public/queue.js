class Node {
    constructor(value) {
      this.value = value;
      this.next = null;
    }
  }
  
export class Queue {
    constructor() {
      this.head = null;
      this.tail = null;
      this.size = 0;
    }
  
    // Enqueue operation
    enqueue(value) {
      const newNode = new Node(value);
      if (!this.head) {
        this.head = newNode;
        this.tail = newNode;
      } else {
        this.tail.next = newNode;
        this.tail = newNode;
      }
      this.size++;
    }
  
    // Dequeue operation
    dequeue() {
      if (!this.head) {
        return null; // Return null if the queue is empty
      }
  
      const removedNode = this.head;
      this.head = this.head.next;
      if (!this.head) {
        this.tail = null; // Update tail if dequeuing the last element
      }
      this.size--;
  
      return removedNode.value;
    }
  
    // Get the size of the queue
    getSize() {
      return this.size;
    }
  
    // Get the front element without removing it
    peek() {
      return this.head ? this.head.value : null;
    }
  
    // Check if the queue is empty
    isEmpty() {
      return this.size === 0;
    }
  }