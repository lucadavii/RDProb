#const n = 5.
#const wmax = 10.
#const hmax = 10.

square(1..n).

{ pos_X(I, 0..wmax-I)} = 1 :- square(I).
{ pos_Y(I, 0..hmax-I)} = 1 :- square(I).

% Non-overlapping constraints
:- square(I), square(J), I < J, pos_X(I, XI), pos_Y(I, YI), pos_X(J, XJ), pos_Y(J, YJ),
   XI + I > XJ, XJ + J > XI, YI + I > YJ, YJ + J > YI.

% Symmetry breaking: place the largest square in the bottom-left corner
:- pos_X(n, X), X > 0.
:- pos_Y(n, Y), Y > 0.

%penalty for area: minimize the area of the bounding rectangle
width(W):- W = #max { X+I : pos_X(I,X), square(I);0 }.
height(H):- H = #max { Y+I : pos_Y(I,Y), square(I);0 }.
area(A) :- width(W), height(H), W>0, H>0, A = W*H.
#minimize { A@1 : area(A) }.

#show pos_X/2.
#show pos_Y/2.
#show width/1.
#show height/1.
#show area/1.

