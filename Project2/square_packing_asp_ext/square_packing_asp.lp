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
% External bound constraints: shrink the rectangle as dictated

#external ext_w(1..wmax).
#external ext_h(1..hmax).

:- pos_X(I,X), ext_w(W), X + I > W.
:- pos_Y(I,Y), ext_h(H), Y + I > H.

#show pos_X/2.
#show pos_Y/2.

