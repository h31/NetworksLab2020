import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.*;

import java.net.ServerSocket;
import java.net.InetSocketAddress;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

public class ServerNIO {

    public static void main(String[] argv) throws Exception {
        new ServerNIO().go(argv);
    }

    private Selector selector;

    public void go(String[] argv)
            throws Exception {
        int port = 1234;

        if (argv.length > 0) {
            port = Integer.parseInt(argv[0]);
        }

        System.out.println("Listening on port " + port);

        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        ServerSocket serverSocket = serverChannel.socket();
        this.selector = Selector.open();

        serverSocket.bind(new InetSocketAddress(port));

        serverChannel.configureBlocking(false);

        serverChannel.register(selector, SelectionKey.OP_ACCEPT);

        List<SocketChannel> channels = new ArrayList<>();
        while (true) {
            int n = selector.select();

            if (n == 0) {
                continue;
            }

            Iterator it = selector.selectedKeys().iterator();

            while (it.hasNext()) {
                SelectionKey key = (SelectionKey) it.next();

                if (key.isAcceptable()) {
                    ServerSocketChannel server =
                            (ServerSocketChannel) key.channel();
                    SocketChannel channel = server.accept();
                    channels.add(channel);
                    System.out.println("channels = " + channels);

                    System.out.println("channel = " + channel);

                    registerChannel(selector, channel,
                            SelectionKey.OP_READ | SelectionKey.OP_WRITE);
                    System.out.println("accept");
                }

                if (key.isReadable()) {
                    readDataFromSocket(key);
                }

                it.remove();
            }
        }
    }

    protected void registerChannel(Selector selector,
                                   SelectableChannel channel, int ops)
            throws Exception {
        if (channel == null) {
            return;
        }

        channel.configureBlocking(false);

        System.out.println("register");
        channel.register(selector, ops);
        System.out.println("afterReg" + channel.register(selector, ops));
    }


    private ByteBuffer buffer = ByteBuffer.allocate(30);


        private void readDataFromSocket(SelectionKey key) throws IOException {
        SocketChannel socketChannel = (SocketChannel) key.channel();
        StringBuilder stringBuilder = new StringBuilder();

        buffer.clear();
        int read;
        while ((read = socketChannel.read(buffer)) > 0) {
            buffer.flip();
            byte[] bytes = new byte[buffer.limit()];
            buffer.get(bytes);
            stringBuilder.append(new String(bytes));
            buffer.clear();
        }
        String msg;
        if (read < 0) {
            msg = "someone left us =(\n";
            System.out.print(msg);
            socketChannel.close();
        } else {
            msg = stringBuilder.toString();
            System.out.print(formatMsg(msg));
            sendMsg(msg);
        }
    }

    private void sendMsg(String msg) throws IOException {
        ByteBuffer byteBuffer = ByteBuffer.wrap(msg.getBytes());
        for (SelectionKey key : selector.keys()) {
            if (key.isValid() && key.channel() instanceof SocketChannel) {
                SocketChannel socketChannel = (SocketChannel) key.channel();
                socketChannel.write(byteBuffer);
                byteBuffer.rewind();
            }
        }
    }


    private String formatMsg(String msg) {
        int d3 = 0;
        do {
            msg = msg.substring(d3);
            if (msg.startsWith("\0")) {
                msg = msg.substring(1);
            }
            int d1 = msg.indexOf("\0");
            if (d1 == -1 || d1 + 1 == msg.length()) {
                System.out.print(msg);
                break;
            }
            int d2 = msg.indexOf("\0", d1 + 1);
            d3 = msg.indexOf("\0", d2 + 1);
            String millisStr = msg.substring(0, d1);
            String name = msg.substring(d1 + 1, d2);
            String text = d3 != -1 ? msg.substring(d2 + 1, d3) : msg.substring(d2 + 1);

            long millisLong = Long.parseLong(millisStr);
            Date time = new Date(millisLong);
            SimpleDateFormat dt1 = new SimpleDateFormat("HH:mm:ss.SSS");
            String dtime = dt1.format(time);
            return ("<" + dtime + "> " + name + ": " + text);
        } while (d3 != -1 && d3 + 1 < msg.length());
        return "";
    }
}


