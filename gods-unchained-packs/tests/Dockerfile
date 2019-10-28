FROM alpine:latest

# Get required packages
RUN apk add --update --no-cache wget autoconf automake openssl libtool libffi-dev python3 npm make g++ git openssl-dev python3-dev

# build the libsecp256k1 library
RUN git clone https://github.com/bitcoin-core/secp256k1.git
RUN cd secp256k1 && ./autogen.sh && ./configure && make && make install

RUN pip3 install --upgrade pip

# Install the Python requirements
COPY tests/requirements.txt /
RUN pip3 install -r requirements.txt

# Download the binary for solc v0.5.0
RUN wget https://github.com/ethereum/solidity/releases/download/v0.5.0/solc-static-linux -O /usr/bin/solc
RUN chmod u+x /usr/bin/solc
RUN solc --version

# Install Ganache
RUN npm install -g ganache-cli

# Copy the contract source code and test suite
COPY ./code /code
COPY ./tests /tests

# Set the working directory to the tests/ dir
WORKDIR /tests

# Compile the solidity contracts
RUN make all

# Create a script for running Ganache and then running the tests (need to sleep to ensure Ganache has initialised)
RUN echo "./ganache-cli-script.sh > /dev/null 2>&1 &sleep 5&&pytest -v tests" > run-tests.sh
RUN chmod u+x run-tests.sh

# "docker run" will execute the tests against the compiled contracts
CMD ./run-tests.sh
