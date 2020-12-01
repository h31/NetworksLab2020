import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.Buffer;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.IntBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.SocketChannel;
import java.nio.charset.Charset;
import java.nio.charset.CharsetDecoder;
import java.text.SimpleDateFormat;
import java.util.*;

import static java.lang.System.currentTimeMillis;

public class ClientNIO {
    static BufferedReader inputUser = null;
    private static String userName = null;
    private static Map<SelectionKey, Boolean> connectMap = new HashMap<>();

    public static boolean processReadySet(Selector selector, Set readySet) throws Exception {
        Iterator iterator = readySet.iterator();
        while (iterator.hasNext()) {
            SelectionKey key = (SelectionKey) iterator.next();
            iterator.remove();
            if (!connectMap.getOrDefault(key, false) && key.isConnectable()) {
                connectMap.put(key, true);
                boolean connected = processConnect(key);
                if (!connected) {
                    return true;
                }
            } else if (key.isConnectable()) {
                System.exit(0);
            }
            if (key.isReadable()) {
                String msg = processRead(key);
                if (!msg.isEmpty()) {
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
                        String finalMsg = "<" + dtime + "> " + name + ": " + text;
                        System.out.println(finalMsg);
                        System.out.flush();
                    } while (d3 != -1 && d3 + 1 < msg.length());
                }
            }
            if (key.isWritable()) {
                try {
                    if (inputUser.ready()) {
                        String userLine = inputUser.readLine();
                        if (!userLine.isEmpty()) {
                            if (userLine.equalsIgnoreCase("bye")) {
                                return true;
                            }
                            String msg = userName + "\0" + userLine;
                            long currentTime = currentTimeMillis();
                            msg = currentTime + "\0" + msg + "\0";
                            SocketChannel sChannel = (SocketChannel) key.channel();
                            ByteBuffer buffer = ByteBuffer.wrap(msg.getBytes());
                            sChannel.write(buffer);
                        }
                    }
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }


            }
        }
        return false;
    }

    public static boolean processConnect(SelectionKey key) throws Exception {
        SocketChannel channel = (SocketChannel) key.channel();
        System.out.print("Press Nick: ");
        userName = inputUser.readLine();
        while (channel.isConnectionPending()) {
            channel.finishConnect();
        }
        return true;
    }

    public static String processRead(SelectionKey key) throws Exception {
        SocketChannel sChannel = (SocketChannel) key.channel();
        ByteBuffer buffer = ByteBuffer.allocate(210000);
        int status = sChannel.read(buffer);
        if (status == -1) {
            System.out.println("status = " + status);
            System.exit(0);
        }
        buffer.flip();
        Charset charset = Charset.forName("UTF-8");
        CharsetDecoder decoder = charset.newDecoder();
        CharBuffer charBuffer = decoder.decode(buffer);
        String msg = charBuffer.toString();
        return msg;
    }

    public static void main(String[] args) throws Exception {
        InetAddress serverIPAddress = InetAddress.getByName("localhost");
        int port = 1234;
        InetSocketAddress serverAddress = new InetSocketAddress(serverIPAddress, port);
        Selector selector = Selector.open();
        SocketChannel channel = SocketChannel.open();
        channel.configureBlocking(false);
        channel.connect(serverAddress);
        int operations = SelectionKey.OP_CONNECT | SelectionKey.OP_READ | SelectionKey.OP_WRITE;
        channel.register(selector, operations);

        inputUser = new BufferedReader(new InputStreamReader(System.in));
        while (true) {
            if (selector.select() > 0) {
                boolean doneStatus = processReadySet(selector, selector.selectedKeys());
                if (doneStatus) {
                    break;
                }
            }
        }
        channel.close();
    }
}
