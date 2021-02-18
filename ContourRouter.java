package routing;

import java.util.ArrayList;
import java.util.List;

import core.Connection;
import core.Settings;
import core.Coord;
import core.DTNHost;
import core.Message;

public class ContourRouter extends ActiveRouter {

	public static final String CONTOUR_SIZE = "ctrSize";
	public static final String GATEWAY_LOCN = "gateway";
	public static final String CROUTING_NS = "ContourRouter"; //name space
	
	private int contourSize;
	private Coord gateway;
	private Coord baseStation;
	/**
	 * Constructor. Creates a new message router based on the settings in
	 * the given Settings object.
	 * @param s The settings object
	 */
	public ContourRouter(Settings s) {
		super(s);
		Settings contourRouterSettings = new Settings(CROUTING_NS);
		int defaultValue = 5;
		this.contourSize = contourRouterSettings.getInt(CONTOUR_SIZE, defaultValue);
		double [] gateway_XY = contourRouterSettings.getCsvDoubles(GATEWAY_LOCN,2);
		double x = gateway_XY[0];
		double y = gateway_XY[1];
		this.gateway = new Coord(x,y);
		this.baseStation = new Coord(1000,1000); //hard-coded for now
	}
	
	/**
	 * Copy constructor.
	 * @param r The router prototype where setting values are copied from
	 */
	protected ContourRouter(ContourRouter r) {
		super(r);
		this.contourSize = r.contourSize;
		this.gateway = r.gateway;
		this.baseStation = r.baseStation;
	}
	
	@Override
	public void update() {
		super.update();
		if (isTransferring() || !canStartTransfer()) {
			return; 
		}
		
		if (exchangeDeliverableMessages() != null) {
			return; 
		}
		
		tryAllMessagesToRelevantConnections();
		
	}
	
	protected Connection tryAllMessagesToRelevantConnections()
	{		
		//list of all connections obtained
		List<Connection> connections = getConnections();
		if (connections.size() == 0 || this.getNrofMessages() == 0) {
			return null;
		}

		//list of all messages obtained
		List<Message> messages = 
			new ArrayList<Message>(this.getMessageCollection());
		this.sortByQueueMode(messages);
		
		for (int i=0, n=connections.size(); i<n; i++) {
			Connection con = connections.get(i);
			DTNHost to = con.getOtherNode(this.getHost());
			
			if(inSpin(this.getHost())) //node in spin phase
			{
				//rejects connections with hosts that are NOT in spin phase
				if(!inSpin(to)) continue;
			}
			else
			{
				//rejects connections with hosts that are NOT closer to gateway/destination
				if(distanceFromGateway(to)>distanceFromGateway(this.getHost()))
					continue;		
			}
			
			Message started = tryAllMessages(con, messages); 
			if (started != null) { 
				return con;
			}
		}
		
		return null;
		
	}
	
	protected double distanceFromGateway(DTNHost node)
	{
		double rGateway = this.gateway.distance(this.baseStation);
		double rNode = node.getLocation().distance(this.baseStation); 
		return Math.abs(rGateway-rNode);
	}
	
	@Override
	protected void transferDone(Connection con) {
		
		if(!inSpin(this.getHost())) //if in approach phase
			/* don't leave a copy for the sender */
			this.deleteMessage(con.getMessage().getId(), false);
	}
	
	@Override
	public MessageRouter replicate() {
		return new ContourRouter(this);
	}
	
	protected boolean inSpin(DTNHost node) { 
		if(distanceFromGateway(node)<contourSize)
		return true;
		else return false;
	}
	

}
